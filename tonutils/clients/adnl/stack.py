import typing as t

from pytoniq_core import Address, Cell, Slice, VmTuple

from tonutils.types import StackItem, StackItems
from tonutils.utils import norm_stack_num, norm_stack_cell


def decode_stack(items: t.List[t.Any]) -> StackItems:
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
