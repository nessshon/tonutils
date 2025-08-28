import typing as t

from pytoniq_core import (
    Cell,
    WalletMessage,
    HashMap,
    begin_cell,
)

from ..base import BaseWallet
from ..get_methods import WalletGetMethods
from ....exceptions import ContractError
from ....types import (
    PublicKey,
    OutActionSendMsg,
    OpCode,
    WalletHighloadV2Config,
    WalletHighloadV2Data,
    WalletHighloadV2Params,
    WalletHighloadV3Config,
    WalletHighloadV3Data,
    WalletHighloadV3Params,
    WalletVersion,
)
from ....utils import build_internal_wallet_msg


class WalletHighloadV2(
    BaseWallet[
        WalletHighloadV2Data,
        WalletHighloadV2Config,
        WalletHighloadV2Params,
    ],
):
    _data_model = WalletHighloadV2Data
    _config_model = WalletHighloadV2Config
    _params_model = WalletHighloadV2Params

    VERSION = WalletVersion.WalletHighloadV2
    MAX_MESSAGES = 254

    @staticmethod
    def _build_messages_dict_cell(messages: t.List[WalletMessage]) -> Cell:
        value_serializer = lambda src, dest: dest.store_cell(src.serialize())
        cell_dict = HashMap(key_size=16, value_serializer=value_serializer)
        for index, message in enumerate(messages):
            cell_dict.set_int_key(index, message)
        return cell_dict.serialize()

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletHighloadV2Params] = None,
    ) -> Cell:
        params = params or self._params_model()

        if params.bounded_id and not (0 <= params.bounded_id < (1 << 64)):
            raise ContractError(
                self,
                f"Invalid bounded_id: {params.bounded_id}. "
                f"Expected 0..{(1 << 64) - 1} (unsigned 64-bit); "
                f"got {params.bounded_id.bit_length()}-bit value.",
            )

        msgs_dict = self._build_messages_dict_cell(messages)

        cell = begin_cell()
        cell.store_uint(self.config.subwallet_id, 32)
        cell.store_uint(params.bounded_id, 64)
        cell.store_dict(msgs_dict)
        return cell.end_cell()

    async def get_public_key(self) -> PublicKey:
        return await WalletGetMethods.get_public_key(
            client=self.client,
            address=self.address,
        )

    async def processed(self, query_id: int) -> bool:
        return await WalletGetMethods.processed(
            client=self.client,
            address=self.address,
            query_id=query_id,
        )


class WalletHighloadV3R1(
    BaseWallet[
        WalletHighloadV3Data,
        WalletHighloadV3Config,
        WalletHighloadV3Params,
    ],
):
    _data_model = WalletHighloadV3Data
    _config_model = WalletHighloadV3Config
    _params_model = WalletHighloadV3Params

    VERSION = WalletVersion.WalletHighloadV3R1
    MAX_MESSAGES = 254 * 254

    @staticmethod
    def _build_internal_transfer(
        actions_cell: Cell,
        params: WalletHighloadV3Params,
    ) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.INTERNAL_TRANSFER, 32)
        cell.store_uint(params.query_id, 64)
        cell.store_ref(actions_cell)
        return cell.end_cell()

    def _build_msg_to_send(
        self,
        messages: t.List[WalletMessage],
        params: WalletHighloadV3Params,
    ) -> WalletMessage:
        msgs_per_pack = 253

        if len(messages) > msgs_per_pack:
            rest = self._build_msg_to_send(messages[msgs_per_pack:], params)
            messages = messages[:msgs_per_pack] + [rest]

        actions_cell, value = Cell.empty(), 0
        for msg in messages:
            action = OutActionSendMsg(msg)
            action_cell = begin_cell()
            action_cell.store_ref(actions_cell)
            action_cell.store_cell(action.serialize())
            actions_cell = action_cell.end_cell()
            value += msg.message.info.value.grams

        value = params.value_to_send if params.value_to_send is not None else value
        body = self._build_internal_transfer(actions_cell, params)
        return build_internal_wallet_msg(self.address, params.send_mode, value, body)

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletHighloadV3Params] = None,
    ) -> Cell:
        params = params or self._params_model()

        if not (5 <= self.config.timeout <= (1 << 22) - 1):
            raise ContractError(
                self,
                f"Invalid timeout: {self.config.timeout} s. "
                f"Expected {5}..{(1 << 22) - 1} s "
                f"(unsigned {22}-bit field).",
            )
        if params.query_id and not (0 <= params.query_id < (1 << 23)):
            raise ContractError(
                self,
                f"Invalid query_id: {params.query_id}. "
                f"Expected 0..{(1 << 23) - 1} (unsigned 23-bit).",
            )
        if not messages:
            raise ContractError(
                self, f"messages list is empty; at least one message is required."
            )

        if len(messages) == 1 and messages[0].message.init is None:
            msg_to_send = messages[0]
        else:
            msg_to_send = self._build_msg_to_send(messages, params)

        cell = begin_cell()
        cell.store_uint(self.config.subwallet_id, 32)
        cell.store_ref(msg_to_send.message.serialize())
        cell.store_uint(params.send_mode, 8)
        cell.store_uint(params.query_id, 23)
        cell.store_uint(params.created_at, 64)
        cell.store_uint(self.config.timeout, 22)
        return cell.end_cell()

    async def _build_sign_msg_cell(
        self,
        signing_msg: Cell,
        signature: bytes,
    ) -> Cell:
        cell = begin_cell()
        cell.store_bytes(signature)
        cell.store_ref(signing_msg)
        return cell.end_cell()

    async def get_public_key(self) -> PublicKey:
        return await WalletGetMethods.get_public_key(
            client=self.client,
            address=self.address,
        )

    async def get_subwallet_id(self) -> int:
        return await WalletGetMethods.get_subwallet_id(
            client=self.client,
            address=self.address,
        )

    async def processed(self, query_id: int, need_clean: bool) -> bool:
        return await WalletGetMethods.processed(
            client=self.client,
            address=self.address,
            query_id=query_id,
            need_clean=need_clean,
        )

    async def get_timeout(self) -> int:
        return await WalletGetMethods.get_timout(
            client=self.client,
            address=self.address,
        )

    async def get_last_clean_time(self) -> int:
        return await WalletGetMethods.get_last_clean_time(
            client=self.client,
            address=self.address,
        )
