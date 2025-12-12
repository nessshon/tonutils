import typing as t

from pytoniq_core import Address, Cell, Slice, VmTuple

from tonutils.types import StackItem, StackItems
from tonutils.utils import norm_stack_num, norm_stack_cell


def decode_stack(items: t.List[t.Any]) -> StackItems:
    """
    Decode VM stack items into internal Python structures.

    Supports:
    - int → int
    - Cell/Slice → normalized cell
    - Address → address cell
    - VmTuple/list → recursive decode
    - None → None

    :param items: Raw VM stack items
    :return: Normalized Python stack values
    """

    out: StackItems = []
    for item in items:
        if item is None:
            out.append(None)
        elif isinstance(item, int):
            out.append(norm_stack_num(item))
        elif isinstance(item, Address):
            out.append(item.to_cell())
        elif isinstance(item, (Cell, Slice)):
            out.append(norm_stack_cell(item))
        elif isinstance(item, VmTuple):
            out.append(decode_stack(item.list))
        elif isinstance(item, list):
            out.append(decode_stack(item))
    return out


def encode_stack(items: t.List[StackItem]) -> t.List[t.Any]:
    """
    Encode Python stack values into VM-compatible format.

    Supports:
    - int → int
    - Cell/Slice → cell/slice
    - Address → cell slice
    - list/tuple → recursive encode

    :param items: Normalized Python stack items
    :return: VM-encoded stack values
    """
    out: t.List[t.Any] = []
    for item in items:
        if isinstance(item, int):
            out.append(item)
        elif isinstance(item, Address):
            out.append(item.to_cell().to_slice())
        elif isinstance(item, (Cell, Slice)):
            out.append(item)
        elif isinstance(item, (list, tuple)):
            out.append(encode_stack(list(item)))
    return out
