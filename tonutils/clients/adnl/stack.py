import typing as t

from pytoniq_core import Address, Cell, Slice, VmTuple

from tonutils.clients.stack import StackCodec
from tonutils.utils import norm_stack_cell, norm_stack_num


class LiteStackCodec(StackCodec):
    """Stack codec for the ADNL lite-server transport."""

    @classmethod
    def decode(cls, raw: t.List[t.Any]) -> t.List[t.Any]:
        """Decode TVM stack items to plain Python types.

        :param raw: Raw TVM stack items.
        :return: Decoded items.
        """
        out: t.List[t.Any] = []
        for item in raw:
            if item is None:
                out.append(None)
            elif isinstance(item, int):
                out.append(norm_stack_num(item))
            elif isinstance(item, Address):
                out.append(item.to_cell())
            elif isinstance(item, (Cell, Slice)):
                out.append(norm_stack_cell(item))
            elif isinstance(item, VmTuple):
                out.append(cls.decode(item.list))
            elif isinstance(item, list):
                out.append(cls.decode(item))
        return out

    @classmethod
    def encode(cls, items: t.List[t.Any]) -> t.List[t.Any]:
        """Encode Python values to TVM stack items.

        :param items: Python values.
        :return: Encoded stack items.
        """
        out: t.List[t.Any] = []
        for item in items:
            if isinstance(item, int):
                out.append(item)
            elif isinstance(item, Address):
                out.append(item.to_cell().to_slice())
            elif isinstance(item, (Cell, Slice)):
                out.append(item)
            elif isinstance(item, list):
                out.append(cls.encode(item))
        return out
