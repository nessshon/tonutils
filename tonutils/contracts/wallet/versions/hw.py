import typing as t

from pytoniq_core import Cell, HashMap, WalletMessage, begin_cell

from tonutils.contracts.opcodes import OpCode
from tonutils.contracts.versions import ContractVersion
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.configs import (
    WalletHighloadV2Config,
    WalletHighloadV3Config,
)
from tonutils.contracts.wallet.messages import InternalMessage
from tonutils.contracts.wallet.methods import (
    GetPublicKeyGetMethod,
    ProcessedGetMethod,
    GetSubwalletIDGetMethod,
    GetLastCleanTimeGetMethod,
    GetTimeoutGetMethod,
)
from tonutils.contracts.wallet.params import (
    WalletHighloadV2Params,
    WalletHighloadV3Params,
)
from tonutils.contracts.wallet.tlb import (
    OutActionSendMsg,
    WalletHighloadV2Data,
    WalletHighloadV3Data,
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
    """Wallet Highload V2 contract."""

    _data_model = WalletHighloadV2Data
    """TlbScheme class for deserializing wallet state data."""

    _config_model = WalletHighloadV2Config
    """Configuration model class for this wallet version."""

    _params_model = WalletHighloadV2Params
    """Transaction parameters model class for this wallet version."""

    VERSION = ContractVersion.WalletHighloadV2
    """Contract version identifier."""

    MAX_MESSAGES = 254
    """Maximum number of messages allowed in a single transaction."""

    @staticmethod
    def _build_messages_dict_cell(messages: t.List[WalletMessage]) -> Cell:
        """
        Build dictionary cell containing indexed messages.

        :param messages: List of wallet messages to serialize
        :return: HashMap cell with messages indexed 0..n-1
        """
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
        """
        Build unsigned message cell for Wallet Highload V2 transaction.

        :param messages: List of wallet messages (max 254)
        :param params: Optional wallet parameters (bounded_id)
        :return: Unsigned message cell ready for signing
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
        cell.store_uint(params.bounded_id, 64)
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
    """Wallet Highload V3 Revision 1 contract."""

    _data_model = WalletHighloadV3Data
    """TlbScheme class for deserializing wallet state data."""

    _config_model = WalletHighloadV3Config
    """Configuration model class for this wallet version."""

    _params_model = WalletHighloadV3Params
    """Transaction parameters model class for this wallet version."""

    VERSION = ContractVersion.WalletHighloadV3R1
    """Contract version identifier."""

    MAX_MESSAGES = 254 * 254
    """Maximum number of messages allowed in a single transaction."""

    @staticmethod
    def _build_internal_transfer(
        actions_cell: Cell,
        params: WalletHighloadV3Params,
    ) -> Cell:
        """
        Build internal transfer message body with out-actions.

        :param actions_cell: Serialized out-actions cell
        :param params: Wallet parameters containing query_id
        :return: Internal transfer message body cell
        """
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
        """
        Build recursive message structure for large message batches.

        Splits messages into packs of 253 and creates nested internal transfers.

        :param messages: List of wallet messages to pack
        :param params: Wallet parameters for internal transfers
        :return: Single wallet message containing all nested messages
        """
        msgs_per_pack = 253

        if len(messages) > msgs_per_pack:
            rest = self._build_msg_to_send(messages[msgs_per_pack:], params)
            messages = messages[:msgs_per_pack] + [rest]

        actions_cell, amount = Cell.empty(), 0
        for msg in messages:
            action = OutActionSendMsg(msg)
            action_cell = begin_cell()
            action_cell.store_ref(actions_cell)
            action_cell.store_cell(action.serialize())
            actions_cell = action_cell.end_cell()
            amount += msg.message.info.value.grams

        value = amount if params.value_to_send is None else params.value_to_send
        body = self._build_internal_transfer(actions_cell, params)
        message = InternalMessage(dest=self.address, value=value, body=body)
        return WalletMessage(send_mode=params.send_mode, message=message)

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletHighloadV3Params] = None,
    ) -> Cell:
        """
        Build unsigned message cell for Wallet Highload V3 transaction.

        :param messages: List of wallet messages (max 254*254)
        :param params: Optional wallet parameters (query_id, send_mode, created_at, value_to_send)
        :return: Unsigned message cell ready for signing
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
                self, f"Messages list is empty; at least one message is required."
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
        """
        Combine signature with unsigned message cell.

        :param signing_msg: Unsigned message cell
        :param signature: Ed25519 signature bytes
        :return: Signed message cell
        """
        cell = begin_cell()
        cell.store_bytes(signature)
        cell.store_ref(signing_msg)
        return cell.end_cell()
