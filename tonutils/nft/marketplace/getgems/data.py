from __future__ import annotations

import time

from pytoniq_core import Address, Cell, TlbScheme, begin_cell


class SaleV3R3Data(TlbScheme):

    def __init__(
            self,
            nft_address: Address,
            owner_address: Address,
            marketplace_address: Address,
            marketplace_fee_address: Address,
            royalty_address: Address,
            marketplace_fee: int,
            royalty_fee: int,
            price: int,
    ) -> None:
        self.nft_address = nft_address
        self.owner_address = owner_address
        self.marketplace_address = marketplace_address
        self.marketplace_fee_address = marketplace_fee_address
        self.royalty_address = royalty_address
        self.marketplace_fee = marketplace_fee
        self.royalty_fee = royalty_fee
        self.price = price

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_bit(0)
            .store_uint(int(time.time()), 32)
            .store_address(self.marketplace_address)
            .store_address(self.nft_address)
            .store_address(self.owner_address)
            .store_coins(self.price)
            .store_ref(
                begin_cell()
                .store_address(self.marketplace_fee_address)
                .store_coins(self.marketplace_fee)
                .store_address(self.royalty_address)
                .store_coins(self.royalty_fee)
                .end_cell()
            )
            .store_uint(0, 32)
            .store_uint(0, 64)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Cell) -> SaleV3R3Data:
        raise NotImplementedError
