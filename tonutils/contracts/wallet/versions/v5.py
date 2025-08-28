import abc
import typing as t

from pytoniq_core import (
    Cell,
    WalletMessage,
    begin_cell,
)

from ..base import BaseWallet
from ..get_methods import WalletGetMethods
from ....exceptions import NotRefreshedError
from ....protocols import ClientProtocol
from ....types import (
    NetworkGlobalID,
    OutActionSendMsg,
    PrivateKey,
    PublicKey,
    WalletV5Config,
    WalletV5BetaConfig,
    WalletV5BetaParams,
    WalletV5BetaData,
    WalletV5Data,
    WalletV5Params,
    WalletVersion,
    WalletV5SubwalletID,
    WorkchainID,
)
from ....utils import calc_valid_until

C = t.TypeVar("C", bound=t.Union[WalletV5Config, WalletV5BetaConfig])
D = t.TypeVar("D", bound=t.Union[WalletV5Data, WalletV5BetaData])
P = t.TypeVar("P", bound=t.Union[WalletV5Params, WalletV5BetaParams])

TWalletV5 = t.TypeVar("TWalletV5", bound="_WalletV5[t.Any, t.Any, t.Any]")


class _WalletV5(BaseWallet[D, C, P], abc.ABC):
    MAX_MESSAGES = 255

    @classmethod
    def from_private_key(
        cls: t.Type[TWalletV5],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[C] = None,
    ) -> TWalletV5:
        config = config or cls._config_model()
        cls._validate_config_type(config)

        if config.subwallet_id is None:
            network_global_id = (
                NetworkGlobalID.TESTNET
                if client.is_testnet
                else NetworkGlobalID.MAINNET
            )
            config.subwallet_id = WalletV5SubwalletID(
                network_global_id=network_global_id
            )

        return super().from_private_key(client, private_key, workchain, config)

    async def _build_sign_msg_cell(
        self,
        signing_msg: Cell,
        signature: bytes,
    ) -> Cell:
        cell = begin_cell()
        cell.store_cell(signing_msg)
        cell.store_bytes(signature)
        return cell.end_cell()

    @classmethod
    def _build_out_actions(cls, messages: t.List[WalletMessage]) -> Cell:
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
    def _pack_actions(cls, actions: Cell) -> Cell: ...

    async def get_public_key(self) -> PublicKey:
        return await WalletGetMethods.get_public_key(
            client=self.client,
            address=self.address,
        )

    async def seqno(self) -> int:
        return await WalletGetMethods.seqno(
            client=self.client,
            address=self.address,
        )


class WalletV5Beta(
    _WalletV5[
        WalletV5BetaData,
        WalletV5BetaConfig,
        WalletV5BetaParams,
    ]
):
    _data_model = WalletV5BetaData
    _config_model = WalletV5BetaConfig
    _params_model = WalletV5BetaParams

    VERSION = WalletVersion.WalletV5Beta

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV5BetaParams] = None,
    ) -> Cell:
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
        cell = begin_cell()
        cell.store_uint(0x00, 1)
        cell.store_ref(actions)
        return cell.end_cell()


class WalletV5R1(
    _WalletV5[
        WalletV5Data,
        WalletV5Config,
        WalletV5Params,
    ]
):
    _data_model = WalletV5Data
    _config_model = WalletV5Config
    _params_model = WalletV5Params

    VERSION = WalletVersion.WalletV5R1

    @property
    def state_data(self) -> WalletV5Data:
        if not (self._state_info and self._state_info.data):
            raise NotRefreshedError(self, "state_data")

        network_global_id = (
            NetworkGlobalID.TESTNET
            if self.client.is_testnet
            else NetworkGlobalID.MAINNET
        )
        cs = self._state_info.data.begin_parse()
        return self._data_model.deserialize(cs, network_global_id)

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV5Params] = None,
    ) -> Cell:
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
        cell = begin_cell()
        cell.store_uint(0x01, 1)
        cell.store_ref(actions)
        cell.store_uint(0x00, 1)
        return cell.end_cell()

    async def get_subwallet_id(self) -> int:
        return await WalletGetMethods.get_subwallet_id(
            client=self.client,
            address=self.address,
        )

    async def get_extensions(self) -> Cell:
        return await WalletGetMethods.get_extensions(
            client=self.client,
            address=self.address,
        )

    async def is_signature_allowed(self) -> bool:
        return await WalletGetMethods.is_signature_allowed(
            client=self.client,
            address=self.address,
        )
