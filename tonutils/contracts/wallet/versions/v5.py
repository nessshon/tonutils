import abc
import typing as t

from pytoniq_core import (
    Address,
    Cell,
    WalletMessage,
    begin_cell,
)

from tonutils.clients.http.provider.tonapi.models import (
    BlockchainMessagePayload,
    GaslessConfigResult,
    GaslessEstimatePayload,
    GaslessEstimateResult,
    GaslessSendPayload,
)
from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.opcodes import OpCode
from tonutils.contracts.versions import ContractVersion
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.configs import (
    WalletV5BetaConfig,
    WalletV5Config,
)
from tonutils.contracts.wallet.messages import (
    ExternalMessage,
    JettonTransferBuilder,
    TONTransferBuilder,
)
from tonutils.contracts.wallet.methods import (
    SeqnoGetMethod,
    GetPublicKeyGetMethod,
    GetSubwalletIDGetMethod,
    GetExtensionsGetMethod,
    IsSignatureAllowedGetMethod,
)
from tonutils.contracts.wallet.params import WalletV5BetaParams, WalletV5Params
from tonutils.contracts.wallet.tlb import OutActionSendMsg, WalletV5SubwalletID
from tonutils.contracts.wallet.tlb import WalletV5BetaData, WalletV5Data
from tonutils.exceptions import ClientError, StateNotLoadedError
from tonutils.types import AddressLike, NetworkGlobalID, PrivateKey, WorkchainID
from tonutils.utils import calc_valid_until, cell_to_hex, to_nano

_C = t.TypeVar("_C", bound=t.Union[WalletV5Config, WalletV5BetaConfig])
_D = t.TypeVar("_D", bound=t.Union[WalletV5Data, WalletV5BetaData])
_P = t.TypeVar("_P", bound=t.Union[WalletV5Params, WalletV5BetaParams])

_TWalletV5 = t.TypeVar("_TWalletV5", bound="_WalletV5[t.Any, t.Any, t.Any]")


class _WalletV5(
    BaseWallet[_D, _C, _P],
    SeqnoGetMethod,
    GetPublicKeyGetMethod,
    abc.ABC,
):
    """Base implementation for Wallet v5."""

    MAX_MESSAGES = 255

    @classmethod
    def from_private_key(
        cls: t.Type[_TWalletV5],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[_C] = None,
    ) -> _TWalletV5:
        """Create wallet from a private key.

        :param client: TON client.
        :param private_key: Ed25519 private key.
        :param workchain: Target workchain.
        :param config: Wallet configuration, or `None`.
        :return: New wallet instance.
        """
        config = config or cls._config_model()
        cls._validate_config_type(config)

        if config.subwallet_id is None:
            network = client.network
            if network == NetworkGlobalID.TETRA:
                network = NetworkGlobalID.MAINNET
            config.subwallet_id = WalletV5SubwalletID(network=network)

        return super().from_private_key(client, private_key, workchain, config)

    async def _build_sign_msg_cell(
        self,
        signing_msg: Cell,
        signature: bytes,
    ) -> Cell:
        """Combine signature with unsigned message cell.

        :param signing_msg: Unsigned message cell.
        :param signature: Ed25519 signature bytes.
        :return: Signed message cell.
        """
        cell = begin_cell()
        cell.store_cell(signing_msg)
        cell.store_bytes(signature)
        return cell.end_cell()

    @classmethod
    def _build_out_actions(cls, messages: t.List[WalletMessage]) -> Cell:
        """Build out-actions list from wallet messages.

        :param messages: Wallet messages to serialize.
        :return: Out-actions `Cell`.
        """
        actions_cell = Cell.empty()

        for msg in messages:
            action = OutActionSendMsg(msg)
            action_cell = begin_cell()
            action_cell.store_ref(actions_cell)
            action_cell.store_cell(action.serialize())
            actions_cell = action_cell.end_cell()

        return actions_cell

    @classmethod
    @abc.abstractmethod
    def _pack_actions(cls, actions: Cell) -> Cell:
        """Pack out-actions with version-specific format.

        :param actions: Out-actions `Cell`.
        :return: Packed actions `Cell`.
        """

    def _gasless_validate_provider(self) -> None:
        """Validate that the client supports gasless transfers.

        :raises ClientError: If the client does not use `TonapiHttpProvider`
            or the network is not mainnet.
        """
        from tonutils.clients.http.provider.tonapi import TonapiHttpProvider

        if not isinstance(self.client.provider, TonapiHttpProvider):
            raise ClientError(
                "Gasless transfers require `TonapiClient`. "
                f"Current client uses `{type(self.client.provider).__name__}`."
            )
        if self.client.network != NetworkGlobalID.MAINNET:
            raise ClientError(
                "Gasless transfers are only supported on MAINNET. "
                f"Current network: `{self.client.network!r}`."
            )

    @staticmethod
    def _gasless_validate_jetton(
        config: GaslessConfigResult,
        jetton_master_address: str,
    ) -> None:
        """Validate that the jetton is supported for gasless payments.

        :param config: Gasless configuration with supported jettons.
        :param jetton_master_address: Raw jetton master address string.
        :raises ClientError: If the jetton is not supported.
        """
        supported = {jetton.master_id for jetton in config.gas_jettons}
        if jetton_master_address not in supported:
            raise ClientError(
                f"Jetton `{jetton_master_address}` is not supported for gasless transfers. "
                f"Supported: {', '.join(supported)}."
            )

    async def _gasless_build_external_msg(
        self,
        estimate_result: GaslessEstimateResult,
        seqno: t.Optional[int] = None,
    ) -> ExternalMessage:
        """Build and sign an external message from gasless estimation result.

        :param estimate_result: Gasless estimation result with messages to sign.
        :param seqno: Sequence number, or `None` to fetch from contract.
        :return: Signed `ExternalMessage`.
        """
        estimated_messages = [
            TONTransferBuilder(
                destination=Address(msg.address),
                amount=int(msg.amount),
                body=Cell.one_from_boc(msg.payload) if msg.payload else None,
            )
            for msg in estimate_result.messages
        ]
        params = t.cast(
            _P,
            self._params_model(
                seqno=seqno,
                valid_until=estimate_result.valid_until,
                op_code=OpCode.AUTH_SIGNED_INTERNAL,
            ),
        )
        return await self.build_external_message(estimated_messages, params)

    async def gasless_estimate(
        self,
        destination: AddressLike,
        jetton_amount: int,
        jetton_master_address: AddressLike,
        response_address: t.Optional[AddressLike] = None,
        custom_payload: t.Optional[Cell] = None,
        forward_payload: t.Optional[t.Union[Cell, str]] = None,
        forward_amount: int = 1,
        amount: int = to_nano("0.05"),
        query_id: int = 0,
        bounce: t.Optional[bool] = None,
    ) -> GaslessEstimateResult:
        """Estimate a gasless jetton transfer via Tonapi relay.

        Builds a jetton transfer message and sends it to the gasless
        estimation endpoint. Parameters mirror `JettonTransferBuilder`.

        :param destination: Recipient address.
        :param jetton_amount: Jetton amount in base units.
        :param jetton_master_address: Jetton master address (also used for gas payment).
        :param response_address: Address for excess funds, or `None` for wallet address.
        :param custom_payload: Custom payload cell, or `None`.
        :param forward_payload: Payload to forward (`Cell` or text), or `None`.
        :param forward_amount: Amount to forward in nanotons.
        :param amount: TON amount attached to the jetton transfer message.
        :param query_id: Query identifier.
        :param bounce: Bounce on error, or `None` for auto-detect.
        :return: `GaslessEstimateResult` with messages to sign and send.
        :raises ClientError: If the client or jetton is not supported.
        """
        raw_jetton_master_address = (
            jetton_master_address.to_str(is_user_friendly=False)
            if isinstance(jetton_master_address, Address)
            else Address(jetton_master_address).to_str(is_user_friendly=False)
        )

        self._gasless_validate_provider()
        config = await self.client.provider.gasless_config()
        self._gasless_validate_jetton(config, raw_jetton_master_address)
        response_address = response_address or Address(config.relay_address)

        builder = JettonTransferBuilder(
            destination=destination,
            jetton_amount=jetton_amount,
            jetton_master_address=jetton_master_address,
            response_address=response_address,
            custom_payload=custom_payload,
            forward_payload=forward_payload,
            forward_amount=forward_amount,
            amount=amount,
            query_id=query_id,
            bounce=bounce,
        )
        message = await builder.build(self)
        boc = cell_to_hex(message.message.serialize())

        assert self._public_key is not None
        return await self.client.provider.gasless_estimate(
            master_id=raw_jetton_master_address,
            payload=GaslessEstimatePayload(
                return_emulation=True,
                wallet_address=self.address.to_str(is_user_friendly=False),
                wallet_public_key=self._public_key.as_hex,
                messages=[BlockchainMessagePayload(boc=boc)],
            ),
        )

    async def gasless_send(
        self,
        estimate_result: GaslessEstimateResult,
        seqno: t.Optional[int] = None,
    ) -> None:
        """Sign and send a gasless transfer from estimation result.

        Builds an external message from the estimation, signs it,
        and sends via the gasless relay.

        :param estimate_result: Result from `gasless_estimate`.
        :param seqno: Sequence number, or `None` to fetch from contract.
        """
        assert self._public_key is not None
        external_msg = await self._gasless_build_external_msg(
            estimate_result=estimate_result,
            seqno=seqno,
        )
        await self.client.provider.gasless_send(
            GaslessSendPayload(
                wallet_public_key=self._public_key.as_hex,
                boc=external_msg.as_hex,
            ),
        )


class WalletV5Beta(
    _WalletV5[
        WalletV5BetaData,
        WalletV5BetaConfig,
        WalletV5BetaParams,
    ]
):
    """Wallet v5 Beta."""

    _data_model = WalletV5BetaData
    _config_model = WalletV5BetaConfig
    _params_model = WalletV5BetaParams
    VERSION = ContractVersion.WalletV5Beta

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV5BetaParams] = None,
    ) -> Cell:
        """Build unsigned message cell.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or `None`.
        :return: Unsigned message cell.
        """
        params = params or self._params_model()

        seqno = (
            params.seqno
            if params.seqno is not None
            else self.state_data.seqno if self.is_active else 0
        )
        valid_until = (
            params.valid_until
            if params.valid_until is not None
            else calc_valid_until(seqno)
        )
        subwallet_id = t.cast(WalletV5SubwalletID, self.config.subwallet_id)

        cell = begin_cell()
        cell.store_uint(params.op_code, 32)
        cell.store_int(subwallet_id.network, 32)
        cell.store_int(subwallet_id.workchain, 8)
        cell.store_uint(subwallet_id.version, 8)
        cell.store_uint(subwallet_id.subwallet_number, 32)
        cell.store_uint(valid_until, 32)
        cell.store_uint(seqno, 32)

        actions = self._build_out_actions(messages)
        cell.store_cell(self._pack_actions(actions))
        return cell.end_cell()

    @classmethod
    def _pack_actions(cls, actions: Cell) -> Cell:
        """Pack out-actions with v5 Beta format (0x00 prefix).

        :param actions: Out-actions `Cell`.
        :return: Packed actions `Cell`.
        """
        cell = begin_cell()
        cell.store_uint(0x00, 1)
        cell.store_ref(actions)
        return cell.end_cell()


class WalletV5R1(
    _WalletV5[
        WalletV5Data,
        WalletV5Config,
        WalletV5Params,
    ],
    GetSubwalletIDGetMethod,
    GetExtensionsGetMethod,
    IsSignatureAllowedGetMethod,
):
    """Wallet v5 Revision 1."""

    _data_model = WalletV5Data
    _config_model = WalletV5Config
    _params_model = WalletV5Params
    VERSION = ContractVersion.WalletV5R1

    @property
    def state_data(self) -> WalletV5Data:
        """Decoded on-chain wallet state data."""
        if not (self._info and self._info.data):
            raise StateNotLoadedError(self, missing="state_data")

        network = self.client.network
        if network == NetworkGlobalID.TETRA:
            network = NetworkGlobalID.MAINNET

        cs = self._info.data.begin_parse()
        return self._data_model.deserialize(cs, network)

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV5Params] = None,
    ) -> Cell:
        """Build unsigned message cell.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or `None`.
        :return: Unsigned message cell.
        """
        params = params or self._params_model()

        seqno = (
            params.seqno
            if params.seqno is not None
            else self.state_data.seqno if self.is_active else 0
        )
        valid_until = (
            params.valid_until
            if params.valid_until is not None
            else calc_valid_until(seqno)
        )
        subwallet_id = t.cast(WalletV5SubwalletID, self.config.subwallet_id)

        cell = begin_cell()
        cell.store_uint(params.op_code, 32)
        cell.store_uint(subwallet_id.pack(), 32)
        cell.store_uint(valid_until, 32)
        cell.store_uint(seqno, 32)

        actions = self._build_out_actions(messages)
        cell.store_cell(self._pack_actions(actions))
        return cell.end_cell()

    @classmethod
    def _pack_actions(cls, actions: Cell) -> Cell:
        """Pack out-actions with v5 R1 format (0x01 prefix + extension flag).

        :param actions: Out-actions `Cell`.
        :return: Packed actions `Cell`.
        """
        cell = begin_cell()
        cell.store_uint(0x01, 1)
        cell.store_ref(actions)
        cell.store_uint(0x00, 1)
        return cell.end_cell()
