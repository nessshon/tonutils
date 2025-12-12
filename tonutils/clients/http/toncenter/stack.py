from __future__ import annotations

import typing as t

from pytoniq_core import Address, Cell, Slice

from tonutils.types import StackTag, StackItem, StackItems
from tonutils.utils import cell_to_b64, norm_stack_num, norm_stack_cell


def decode_stack(items: t.List[t.Any]) -> StackItems:
    """
    Decode Toncenter TVM stack format into internal python structures.

    Converts Toncenter stack elements into native Python values:
    - NUM → int
    - CELL/SLICE → Cell or Address (auto-detected)
    - LIST/TUPLE → recursively decoded lists
    - NULL → None

    :param items: Raw stack items as returned by Toncenter
    :return: Normalized list of decoded stack values
    """
    out: StackItems = []
    for item in items:
        if not (isinstance(item, list) and len(item) == 2):
            continue
        tag, payload = item
        if tag == StackTag.NULL:
            out.append(None)
        elif tag == StackTag.NUM.value:
            out.append(norm_stack_num(payload))
        elif tag in (
            StackTag.CELL.value,
            StackTag.TVM_CELL.value,
            StackTag.SLICE.value,
            StackTag.TVM_SLICE.value,
        ):
            out.append(norm_stack_cell((payload or {}).get("bytes")))
        elif tag in (StackTag.LIST.value, StackTag.TUPLE.value):
            elements = (payload or {}).get("elements") or []
            out.append(decode_stack(elements) if len(elements) > 0 else None)
    return out


def encode_stack(items: t.List[StackItem]) -> t.List[list]:
    """
    Encode Python stack values into Toncenter-compatible TVM stack format.

    Supports:
    - int → NUM
    - Cell → TVM_CELL
    - Slice → TVM_SLICE
    - list/tuple → LIST/TUPLE (recursive)
    - Address → encoded as TVM_CELL

    :param items: List of python TVM stack values
    :return: Encoded stack items suitable for Toncenter API
    """
    out: t.List[t.Any] = []
    for item in items:
        tpe = StackTag.of(item)
        if tpe is StackTag.NUM:
            out.append([StackTag.NUM.value, str(t.cast(str, item))])
        elif tpe is StackTag.CELL:
            cell = item.to_cell() if isinstance(item, Address) else t.cast(Cell, item)
            out.append([StackTag.TVM_CELL.value, cell_to_b64(cell)])
        elif tpe is StackTag.SLICE:
            cell = t.cast(Slice, item).to_cell()
            out.append([StackTag.TVM_SLICE.value, cell_to_b64(cell)])
        elif tpe in (StackTag.LIST, StackTag.TUPLE):
            out.append([tpe.value, {"elements": encode_stack(t.cast(list, item))}])
    return out
