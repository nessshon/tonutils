from ton_core import (
    Builder,
    Cell,
    ContractVersion,
    HashMap,
    OpCode,
    OutActionSendMsg,
    WalletHighloadV2Config,
    WalletHighloadV2Data,
    WalletHighloadV2Params,
    WalletHighloadV3Config,
    WalletHighloadV3Data,
    WalletHighloadV3Params,
    WalletMessage,
    begin_cell,
)

from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.messages import InternalMessage
from tonutils.contracts.wallet.methods import (
    GetLastCleanTimeGetMethod,
    GetPublicKeyGetMethod,
    GetSubwalletIDGetMethod,
    GetTimeoutGetMethod,
    ProcessedGetMethod,
)
from tonutils.exceptions import ContractError


class WalletHighloadV2(
    BaseWallet[
        WalletHighloadV2Data,
        WalletHighloadV2Config,
        WalletHighloadV2Params,
    ],
    GetPublicKeyGetMethod,
    ProcessedGetMethod,
):
    """Highload Wallet v2 -- mass sends via ``HashMap``, up to 254 messages per transaction."""

    _data_model = WalletHighloadV2Data
    _config_model = WalletHighloadV2Config
    _params_model = WalletHighloadV2Params
    VERSION = ContractVersion.WalletHighloadV2
    MAX_MESSAGES = 254

    @staticmethod
    def _build_messages_dict_cell(messages: list[WalletMessage]) -> Cell:
        """Build ``HashMap`` cell with indexed messages.

        :param messages: Wallet messages to serialize.
        :return: Serialized ``HashMap`` cell.
        """

        def value_serializer(src: WalletMessage, dest: Builder) -> Builder:
            return dest.store_cell(src.serialize())

        cell_dict = HashMap(key_size=16, value_serializer=value_serializer)
        for index, message in enumerate(messages):
            cell_dict.set_int_key(index, message)
        return cell_dict.serialize() or Cell.empty()

    async def _build_msg_cell(
        self,
        messages: list[WalletMessage],
        params: WalletHighloadV2Params | None = None,
    ) -> Cell:
        """Build unsigned message cell.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or ``None``.
        :return: Unsigned message cell.
        :raises ContractError: If ``bounded_id`` is out of range.
        """
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
        cell.store_uint(params.bounded_id or 0, 64)
        cell.store_dict(msgs_dict)
        return cell.end_cell()


class WalletHighloadV3R1(
    BaseWallet[
        WalletHighloadV3Data,
        WalletHighloadV3Config,
        WalletHighloadV3Params,
    ],
    GetPublicKeyGetMethod,
    ProcessedGetMethod,
    GetSubwalletIDGetMethod,
    GetLastCleanTimeGetMethod,
    GetTimeoutGetMethod,
):
    """Highload Wallet v3 Revision 1 -- recursive out-action packing, up to 64516 messages per transaction."""

    _data_model = WalletHighloadV3Data
    _config_model = WalletHighloadV3Config
    _params_model = WalletHighloadV3Params
    VERSION = ContractVersion.WalletHighloadV3R1
    MAX_MESSAGES = 254 * 254

    @staticmethod
    def _build_internal_transfer(
        actions_cell: Cell,
        params: WalletHighloadV3Params,
    ) -> Cell:
        """Build internal transfer body with out-actions.

        :param actions_cell: Serialized out-actions cell.
        :param params: Transaction parameters.
        :return: Internal transfer body ``Cell``.
        """
        cell = begin_cell()
        cell.store_uint(OpCode.INTERNAL_TRANSFER, 32)
        cell.store_uint(params.query_id or 0, 64)
        cell.store_ref(actions_cell)
        return cell.end_cell()

    def _build_msg_to_send(
        self,
        messages: list[WalletMessage],
        params: WalletHighloadV3Params,
    ) -> WalletMessage:
        """Build recursive message structure for large batches.

        Splits messages into packs of 253 with nested internal transfers.

        :param messages: Wallet messages to pack.
        :param params: Transaction parameters.
        :return: Single ``WalletMessage`` containing all nested messages.
        """
        msgs_per_pack = 253

        if len(messages) > msgs_per_pack:
            rest = self._build_msg_to_send(messages[msgs_per_pack:], params)
            messages = [*messages[:msgs_per_pack], rest]

        actions_cell, amount = Cell.empty(), 0
        for msg in messages:
            action = OutActionSendMsg(msg)
            action_cell = begin_cell()
            action_cell.store_ref(actions_cell)
            action_cell.store_cell(action.serialize())
            actions_cell = action_cell.end_cell()
            info = msg.message.info
            if hasattr(info, "value"):
                amount += info.value.grams

        value = amount if params.value_to_send is None else params.value_to_send
        body = self._build_internal_transfer(actions_cell, params)
        message = InternalMessage(dest=self.address, value=value, body=body)
        return WalletMessage(send_mode=params.send_mode, message=message)

    async def _build_msg_cell(
        self,
        messages: list[WalletMessage],
        params: WalletHighloadV3Params | None = None,
    ) -> Cell:
        """Build unsigned message cell.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or ``None``.
        :return: Unsigned message cell.
        :raises ContractError: If timeout, query_id, or messages are invalid.
        """
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
                self, "Messages list is empty; at least one message is required."
            )

        if len(messages) == 1 and messages[0].message.init is None:
            msg_to_send = messages[0]
        else:
            msg_to_send = self._build_msg_to_send(messages, params)

        cell = begin_cell()
        cell.store_uint(self.config.subwallet_id, 32)
        cell.store_ref(msg_to_send.message.serialize())
        cell.store_uint(params.send_mode, 8)
        cell.store_uint(params.query_id or 0, 23)
        cell.store_uint(params.created_at or 0, 64)
        cell.store_uint(self.config.timeout, 22)
        return cell.end_cell()

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
        cell.store_bytes(signature)
        cell.store_ref(signing_msg)
        return cell.end_cell()
