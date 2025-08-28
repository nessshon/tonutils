import typing as t
from enum import Enum

from pytoniq_core import Address, Cell, Slice


class StackItemType(str, Enum):
    NUM = "num"
    CELL = "cell"
    TVMCELL = "tvm.Cell"
    SLICE = "slice"
    TVMSLICE = "tvm.Slice"
    TUPLE = "tuple"


StackItemLike = t.Optional[t.Union[Address, Cell, Slice, int]]
StackItemsLike = t.List[t.Union[StackItemLike, t.List[StackItemLike]]]
