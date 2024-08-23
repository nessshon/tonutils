from __future__ import annotations

from random import random
from typing import Union, Optional

from pytoniq_core import Address, Cell, Slice, TlbScheme, begin_cell


class SubdomainManagerData(TlbScheme):

    def __init__(
            self,
            admin_address: Union[Address, str],
            domains: Optional[Cell] = None,
            seed: Optional[int] = None,
    ) -> None:
        if isinstance(admin_address, str):
            admin_address = Address(admin_address)

        if seed is None:
            seed = int(random() * 1e9)

        self.admin_address = admin_address
        self.domains = domains
        self.seed = seed

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(self.seed, 64)
            .store_address(self.admin_address)
            .store_maybe_ref(self.domains)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> SubdomainManagerData:
        raise NotImplementedError
