import typing as t

from pytoniq_core import Address, Cell, Slice

from tonutils.clients.stack import StackCodec
from tonutils.utils import cell_to_b64, cell_to_hex, norm_stack_cell, norm_stack_num


class ToncenterStackCodec(StackCodec):
    """Stack codec for the Toncenter v2 HTTP API."""

    @classmethod
    def _decode_entry(cls, entry: t.Dict[str, t.Any]) -> t.Any:
        """Decode a single `@type`-based nested entry.

        :param entry: Raw dict with `@type` key.
        :return: Decoded Python value.
        """
        atype = entry.get("@type", "")

        if atype == "tvm.stackEntryNumber":
            return norm_stack_num((entry.get("number") or {}).get("number"))  # type: ignore[arg-type]

        if atype in ("tvm.stackEntryCell", "tvm.stackEntryBuilder"):
            key = "cell" if atype == "tvm.stackEntryCell" else "builder"
            return norm_stack_cell((entry.get(key) or {}).get("bytes"))

        if atype == "tvm.stackEntrySlice":
            return norm_stack_cell((entry.get("slice") or {}).get("bytes"))

        if atype in ("tvm.stackEntryTuple", "tvm.stackEntryList"):
            key = "tuple" if atype == "tvm.stackEntryTuple" else "list"
            elements = (entry.get(key) or {}).get("elements") or []
            return [cls._decode_entry(el) for el in elements]

        return None

    @classmethod
    def decode(cls, raw: t.List[t.Any]) -> t.List[t.Any]:
        """Decode Toncenter `[tag, payload]` stack pairs.

        :param raw: Raw stack items from the API.
        :return: Decoded Python values.
        """
        out: t.List[t.Any] = []

        for item in raw:
            if not (isinstance(item, list) and len(item) == 2):
                continue

            tag, payload = item[0], item[1]

            if tag == "null":
                out.append(None)
            elif tag == "num":
                out.append(norm_stack_num(payload))
            elif tag in ("cell", "tvm.Cell", "slice", "tvm.Slice"):
                out.append(norm_stack_cell((payload or {}).get("bytes")))
            elif tag in ("tuple", "list"):
                elements = (payload or {}).get("elements") or []
                out.append([cls._decode_entry(el) for el in elements])

        return out

    @classmethod
    def encode(cls, items: t.List[t.Any]) -> t.List[t.Any]:
        """Encode Python values to Toncenter stack format.

        :param items: Python stack values.
        :return: Encoded `[tag, payload]` pairs.
        """
        out: t.List[t.Any] = []

        for item in items:
            if isinstance(item, int):
                out.append(["num", str(item)])
            elif isinstance(item, Address):
                out.append(["tvm.Cell", cell_to_b64(item.to_cell())])
            elif isinstance(item, Cell):
                out.append(["tvm.Cell", cell_to_b64(item)])
            elif isinstance(item, Slice):
                out.append(["tvm.Slice", cell_to_b64(item.to_cell())])
            elif isinstance(item, list):
                out.append(["tuple", {"elements": cls.encode(item)}])

        return out


class TonapiStackCodec(StackCodec):
    """Stack codec for the Tonapi v2 HTTP API."""

    @classmethod
    def decode(cls, raw: t.List[t.Any]) -> t.List[t.Any]:
        """Decode Tonapi `{"type": ..., <type>: <value>}` stack dicts.

        :param raw: Raw stack items from the API.
        :return: Decoded Python values.
        """
        out: t.List[t.Any] = []

        for item in raw:
            if not isinstance(item, dict):
                continue

            tpe = item.get("type", "")

            if tpe == "null":
                out.append(None)
            elif tpe == "num":
                out.append(norm_stack_num(item.get("num")))  # type: ignore[arg-type]
            elif tpe == "cell":
                out.append(norm_stack_cell(item.get("cell")))
            elif tpe == "slice":
                out.append(norm_stack_cell(item.get("slice")))
            elif tpe in ("tuple", "list"):
                out.append(cls.decode(item.get(tpe) or []))

        return out

    @classmethod
    def encode(cls, items: t.List[t.Any]) -> t.List[str]:
        """Encode Python values to hex strings for the Tonapi query parameter.

        :param items: Python stack values.
        :return: Hex-encoded strings.
        """
        out: t.List[str] = []

        for item in items:
            if isinstance(item, int):
                out.append(hex(item))
            elif isinstance(item, Address):
                out.append(cell_to_hex(item.to_cell()))
            elif isinstance(item, Cell):
                out.append(cell_to_hex(item))
            elif isinstance(item, Slice):
                out.append(cell_to_hex(item.to_cell()))

        return out
