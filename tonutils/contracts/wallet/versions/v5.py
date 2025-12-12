import abc
import typing as t

from pytoniq_core import Cell, WalletMessage, begin_cell

from tonutils.contracts.versions import ContractVersion
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.configs import (
    WalletV5BetaConfig,
    WalletV5Config,
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
from tonutils.exceptions import NotRefreshedError
from tonutils.protocols.client import ClientProtocol
from tonutils.types import NetworkGlobalID, PrivateKey, WorkchainID
from tonutils.utils import calc_valid_until

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
    """Base implementation for Wallet V5 contracts."""

    MAX_MESSAGES = 255
    """Maximum number of messages allowed in a single transaction."""

    @classmethod
    def from_private_key(
        cls: t.Type[_TWalletV5],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[_C] = None,
    ) -> _TWalletV5:
        """
        Create wallet instance from a private key.

        :param client: TON client for blockchain interactions
        :param private_key: Ed25519 PrivateKey instance
        :param workchain: Target workchain (default: BASECHAIN)
        :param config: Optional wallet configuration
        :return: New wallet instance
        """
        config = config or cls._config_model()
        cls._validate_config_type(config)

        if config.subwallet_id is None:
            config.subwallet_id = WalletV5SubwalletID(network_global_id=client.network)

        return super().from_private_key(client, private_key, workchain, config)

    async def _build_sign_msg_cell(
        self,
        signing_msg: Cell,
        signature: bytes,
    ) -> Cell:
        """
        Combine signature with unsigned message cell.

        :param signing_msg: Unsigned message cell
        :param signature: Ed25519 signature bytes
        :return: Signed message cell
        """
        cell = begin_cell()
        cell.store_cell(signing_msg)
        cell.store_bytes(signature)
        return cell.end_cell()

    @classmethod
    def _build_out_actions(cls, messages: t.List[WalletMessage]) -> Cell:
        """
        Build out-actions list from wallet messages.

        :param messages: List of wallet messages to serialize
        :return: Cell containing serialized out-actions
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
        """
        Pack out-actions cell with version-specific format.

        :param actions: Serialized out-actions cell
        :return: Packed actions cell ready for inclusion in message
        """


class WalletV5Beta(
    _WalletV5[
        WalletV5BetaData,
        WalletV5BetaConfig,
        WalletV5BetaParams,
    ]
):
    """Wallet V5 Beta contract."""

    _data_model = WalletV5BetaData
    """TlbScheme class for deserializing wallet state data."""

    _config_model = WalletV5BetaConfig
    """Configuration model class for this wallet version."""

    _params_model = WalletV5BetaParams
    """Transaction parameters model class for this wallet version."""

    VERSION = ContractVersion.WalletV5Beta
    """Contract version identifier."""

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV5BetaParams] = None,
    ) -> Cell:
        """
        Build unsigned message cell for Wallet V5 Beta transaction.

        :param messages: List of wallet messages (max 255 for V5)
        :param params: Optional wallet parameters (seqno, valid_until, op_code)
        :return: Unsigned message cell ready for signing
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
        cell.store_int(subwallet_id.network_global_id, 32)
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
        """
        Pack out-actions cell with V5 Beta format.

        :param actions: Serialized out-actions cell
        :return: Packed actions cell with 0x00 prefix
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
    """Wallet V5 Revision 1 contract."""

    _data_model = WalletV5Data
    """TlbScheme class for deserializing wallet state data."""

    _config_model = WalletV5Config
    """Configuration model class for this wallet version."""

    _params_model = WalletV5Params
    """Transaction parameters model class for this wallet version."""

    VERSION = ContractVersion.WalletV5R1
    """Contract version identifier."""

    @property
    def state_data(self) -> WalletV5Data:
        """
        Decoded on-chain wallet state data.

        :return: Typed wallet data
        """
        if not (self._state_info and self._state_info.data):
            raise NotRefreshedError(self, "state_data")

        network_global_id = (
            NetworkGlobalID.TESTNET if self.client.network else NetworkGlobalID.MAINNET
        )
        cs = self._state_info.data.begin_parse()
        return self._data_model.deserialize(cs, network_global_id)

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV5Params] = None,
    ) -> Cell:
        """
        Build unsigned message cell for Wallet V5 R1 transaction.

        :param messages: List of wallet messages (max 255 for V5)
        :param params: Optional wallet parameters (seqno, valid_until, op_code)
        :return: Unsigned message cell ready for signing
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
        """
        Pack out-actions cell with V5 R1 format.

        :param actions: Serialized out-actions cell
        :return: Packed actions cell with 0x01 prefix and extension flag
        """
        cell = begin_cell()
        cell.store_uint(0x01, 1)
        cell.store_ref(actions)
        cell.store_uint(0x00, 1)
        return cell.end_cell()
