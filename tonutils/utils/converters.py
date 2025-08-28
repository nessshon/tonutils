import base64
import hashlib
import typing as t

from pytoniq_core import (
    Cell,
    Slice,
    MessageAny,
    begin_cell,
)


def to_cell(x: t.Union[str, bytes, Cell, Slice]) -> Cell:
    if isinstance(x, Slice):
        x = x.to_cell()
    elif isinstance(x, str):
        x = Cell.one_from_boc(x)
    elif isinstance(x, bytes):
        x = Cell.one_from_boc(x.hex())
    return x


def cell_to_hex(c: t.Union[str, bytes, Cell, Slice]) -> str:
    return to_cell(c).to_boc().hex()


def cell_to_b64(c: Cell) -> str:
    return base64.b64encode(c.to_boc()).decode()


def cell_hash(c: Cell) -> int:
    return int.from_bytes(c.hash, "big")


def slice_hash(s: Slice) -> int:
    return int.from_bytes(s.to_cell().hash, "big")


def string_hash(s: str) -> int:
    data = begin_cell().store_snake_string(s).end_cell().get_data_bytes()
    return int.from_bytes(hashlib.sha256(data).digest(), "big")


def normalize_hash(message: t.Union[MessageAny, str]) -> str:
    if isinstance(message, str):
        message = MessageAny.deserialize(Slice.one_from_boc(message))
    if not message.is_external:
        return message.serialize().hash.hex()

    cell = begin_cell()
    cell.store_uint(2, 2)
    cell.store_address(None)
    cell.store_address(message.info.dest)
    cell.store_coins(0)
    cell.store_bool(False)
    cell.store_bool(True)
    cell.store_ref(message.body)
    return cell.end_cell().hash.hex()
