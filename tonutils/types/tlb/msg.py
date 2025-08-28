from __future__ import annotations

from pytoniq_core import (
    Cell,
    Slice,
    TlbScheme,
    begin_cell,
    WalletMessage,
    MessageAny,
)

from ...exceptions import UnexpectedOpCodeError
from ...types.opcodes import OpCode


class OutActionSendMsg(TlbScheme):

    def __init__(self, message: WalletMessage) -> None:
        self.message = message

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.OUT_ACTION_SEND_MSG, 32)
        cell.store_uint(self.message.send_mode, 8)
        cell.store_ref(self.message.message.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> OutActionSendMsg:
        op_code = cs.load_uint(32)
        if op_code == OpCode.OUT_ACTION_SEND_MSG:
            send_mode = cs.load_uint(8)
            message_slice = cs.load_ref().begin_parse()
            message = MessageAny.deserialize(message_slice)
            return cls(message=WalletMessage(send_mode, message))
        raise UnexpectedOpCodeError(cls, OpCode.OUT_ACTION_SEND_MSG, op_code)
