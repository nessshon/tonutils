from __future__ import annotations

import typing as t

from pytoniq_core import Address, Slice

from tonutils.types import StackTag, StackItem, StackItems
from tonutils.utils import cell_to_hex, norm_stack_num, norm_stack_cell


def decode_stack(items: t.List[t.Any]) -> StackItems:
    """
    Decode Tonapi TVM stack format into internal Python structures.

    Tonapi represents stack items as dictionaries with a "type" key and
    a value under the same key. This function converts them into:
    - NUM → int
    - CELL/SLICE → Cell or Address (auto-detected)
    - LIST/TUPLE → nested Python lists
    - NULL → None

    :param items: Raw stack items as returned by Tonapi
    :return: Normalized list of decoded stack values
    """
    out: StackItems = []
    for item in items:
        if not isinstance(item, dict):
            continue
        tpe = item.get("type")
        val = item.get(tpe)
        if tpe == StackTag.NULL.value:
            out.append(None)
        elif tpe == StackTag.NUM.value and val is not None:
            out.append(norm_stack_num(t.cast(str | int, val)))
        elif tpe in (StackTag.CELL.value, StackTag.SLICE.value):
            out.append(norm_stack_cell(val))
        elif tpe in (StackTag.LIST.value, StackTag.TUPLE.value):
            inner: t.List[t.Any] = []
            for el in val or []:
                inner.append(decode_stack([el])[0] if isinstance(el, dict) else el)
            out.append(inner)
    return out


def encode_stack(items: t.List[StackItem]) -> t.List[t.Any]:
    """
    Encode Python TVM stack values into Tonapi-compatible format.

    Produces values expected by Tonapi query parameters:
    - int → hex string
    - Cell/Address → hex BoC string
    - Slice → hex BoC string
    - list/tuple → recursively encoded list

    :param items: List of python TVM stack values
    :return: Encoded stack items suitable for Tonapi API
    """
    out: t.List[t.Any] = []
    for item in items:
        tpe = StackTag.of(item)
        if tpe == StackTag.NUM:
            out.append(hex(t.cast(int, item)))
        elif tpe == StackTag.CELL:
            cell = item.to_cell() if isinstance(item, Address) else item
            out.append(cell_to_hex(cell))
        elif tpe == StackTag.SLICE:
            cell = t.cast(Slice, item).to_cell()
            out.append(cell_to_hex(cell))
        elif tpe in (StackTag.LIST, StackTag.TUPLE):
            out.append(encode_stack(t.cast(list, item)))
    return out
