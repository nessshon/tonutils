from __future__ import annotations

from pytoniq_core import Address, Cell, TlbScheme, begin_cell, Slice


class RoyaltyParams(TlbScheme):

    def __init__(
            self,
            base: int,
            factor: int,
            address: Address,
    ) -> None:
        self.base = base
        self.factor = factor
        self.address = address

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(self.factor, 16)
            .store_uint(self.base, 16)
            .store_address(self.address)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> RoyaltyParams:
        raise NotImplementedError
