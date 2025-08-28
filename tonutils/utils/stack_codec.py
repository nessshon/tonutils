from __future__ import annotations

import typing as t

from pytoniq_core import (
    Address,
    Cell,
    Slice,
    VmTuple,
)

from . import to_cell
from ..types.client import ClientType
from ..types.stack import (
    StackItemType,
    StackItemLike,
    StackItemsLike,
)


class StackCodec:

    def __init__(self, source: ClientType) -> None:
        self.source = source

    @classmethod
    def _maybe_addr(
        cls,
        v: t.Union[Cell, Slice],
    ) -> t.Optional[t.Union[Address, Cell, Slice]]:
        try:
            s = v.copy().begin_parse() if isinstance(v, Cell) else v.copy()
            tag = s.load_uint(2)
            if tag == 0 and len(s.bits) == 0:
                return None
            if tag == 2 and len(s.bits) == 265:
                s.skip_bits(1)
                wc = s.load_int(8)
                hash_part = s.load_bytes(32)
                return Address((wc, hash_part))
        except (Exception,):
            pass
        return v

    @classmethod
    def _normalize_num(cls, n: t.Union[str, int]) -> int:
        if isinstance(n, str):
            try:
                return int(n, 0)
            except ValueError:
                pass
        return int(n)

    @classmethod
    def _normalize_cell(
        cls,
        c: t.Union[Cell, Slice, str],
    ) -> t.Optional[t.Union[Address, Cell]]:
        cell = to_cell(c)
        return cls._maybe_addr(cell)

    def _normalize_tuple(self, items: t.List[t.Any]) -> StackItemsLike:
        out = []
        if self.source == ClientType.TONAPI:
            out.extend(self.deserialize_items(items))
        elif self.source == ClientType.LITESERVER:
            out.extend(self.deserialize_items(items))
        elif self.source == ClientType.TONCENTER:
            for el in items:
                el_tpe = (el or {}).get("@type", "")
                if el_tpe.endswith("stackEntryCell"):
                    cell = el.get("cell") or {}
                    val = self._normalize_cell(cell.get("bytes"))
                elif el_tpe.endswith("stackEntrySlice"):
                    sl = el.get("slice") or {}
                    val = self._normalize_cell(sl.get("bytes"))
                elif el_tpe.endswith("stackEntryNumber"):
                    number = el.get("number") or {}
                    num = number.get("number")
                    if num is None:
                        continue
                    val = self._normalize_num(num)
                elif el_tpe.endswith("tuple"):
                    inner = el.get("elements") or []
                    val = self._normalize_tuple(inner)
                else:
                    continue
                out.append(val)
        return out

    def deserialize_items(self, items: t.List[t.Any]) -> StackItemsLike:
        out = []
        normalizer = {
            StackItemType.NUM: lambda x: self._normalize_num(x),
            StackItemType.CELL: lambda x: self._normalize_cell(x),
            StackItemType.SLICE: lambda x: self._normalize_cell(x),
            StackItemType.TUPLE: lambda x: self._normalize_tuple(x),
        }
        for item in items:
            if self.source == ClientType.TONAPI:
                if not isinstance(item, dict):
                    continue
                tpe = StackItemType(item.get("type"))
                if tpe in StackItemType:
                    item = item.get(tpe.value)
                else:
                    continue
            elif self.source == ClientType.TONCENTER:
                if not (isinstance(item, list) and len(item) == 2):
                    continue
                tpe, item = StackItemType(item[0]), item[1]
                if tpe in (StackItemType.CELL, StackItemType.SLICE):
                    item = item.get("bytes")
                elif tpe == StackItemType.TUPLE:
                    item = item.get("elements") or []
                elif tpe == StackItemType.NUM:
                    pass
            elif self.source == ClientType.LITESERVER:
                if isinstance(item, Address):
                    tpe = StackItemType.CELL
                    item = item.to_cell()
                elif isinstance(item, int):
                    tpe = StackItemType.NUM
                elif isinstance(item, Cell):
                    tpe = StackItemType.CELL
                elif isinstance(item, Slice):
                    tpe = StackItemType.SLICE
                elif isinstance(item, VmTuple):
                    tpe = StackItemType.TUPLE
                    item = item.list
                else:
                    out.append(item)
                    continue
            callback = normalizer.get(tpe)
            if callback is not None:
                out.append(callback(item))
        return out

    def serialize_items(self, items: t.List[StackItemLike]) -> t.Any:
        from ..utils import cell_to_b64

        out = []
        for item in items:
            if self.source == ClientType.TONAPI:
                value_serializer = {
                    int: lambda x: int(x),
                    Cell: lambda x: cell_to_b64(x),
                    Slice: lambda x: cell_to_b64(x.to_cell()),
                    Address: lambda x: x.to_str(is_user_friendly=False),
                }
                callback = value_serializer[type(item)]
                if callback is not None:
                    out.append(callback(item))
            elif self.source == ClientType.TONCENTER:
                value_serializer = {
                    int: lambda x: hex(x),
                    Cell: lambda x: cell_to_b64(x),
                    Slice: lambda x: cell_to_b64(x.to_cell()),
                    Address: lambda x: cell_to_b64(x.to_cell()),
                }
                callback = value_serializer[type(item)]
                if callback is not None:
                    if isinstance(item, int):
                        tpe = StackItemType.NUM
                    elif isinstance(item, Slice):
                        tpe = StackItemType.TVMSLICE
                    elif isinstance(item, (Address, Cell)):
                        tpe = StackItemType.TVMCELL
                    else:
                        continue
                    out.append([tpe.value, callback(item)])
            elif self.source == ClientType.LITESERVER:
                value_serializer = {
                    int: lambda x: int(x),
                    Cell: lambda x: x,
                    Slice: lambda x: x,
                    Address: lambda x: x.to_cell().to_slice(),
                }
                callback = value_serializer[type(item)]
                if callback is not None:
                    out.append(callback(item))
        return out

    def decode(self, items: t.List[t.Any]) -> StackItemsLike:
        return self.deserialize_items(items)

    def encode(self, items: t.List[StackItemLike]) -> t.Any:
        return self.serialize_items(items)
