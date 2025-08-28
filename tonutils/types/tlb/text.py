from __future__ import annotations

from pytoniq_core import (
    Cell,
    Slice,
    TlbScheme,
    begin_cell,
)

from ...exceptions import UnexpectedOpCodeError
from ...types.opcodes import OpCode


class TextComment(TlbScheme):

    def __init__(self, text: str) -> None:
        self.text = text

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.TEXT_COMMENT, 32)
        cell.store_snake_string(self.text)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TextComment:
        op_code = cs.load_uint(32)
        if op_code == OpCode.TEXT_COMMENT:
            return cls(cs.load_snake_string())
        raise UnexpectedOpCodeError(cls, OpCode.TEXT_COMMENT, op_code)


class EncryptedTextComment(TlbScheme):

    def __init__(self, pub_xor: bytes, msg_key: bytes, ciphertext: bytes) -> None:
        self.pub_xor = pub_xor
        self.msg_key = msg_key
        self.ciphertext = ciphertext

    def serialize(self) -> Cell:
        payload = self.pub_xor + self.msg_key + self.ciphertext
        cell = begin_cell()
        cell.store_uint(OpCode.ENCRYPTED_TEXT_COMMENT, 32)
        cell.store_snake_bytes(payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> EncryptedTextComment:
        op_code = cs.load_uint(32)
        if op_code == OpCode.ENCRYPTED_TEXT_COMMENT:
            payload = cs.load_snake_bytes()
            return cls(payload[:32], payload[32:48], payload[48:])
        raise UnexpectedOpCodeError(cls, OpCode.ENCRYPTED_TEXT_COMMENT, op_code)
