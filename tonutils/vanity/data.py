from __future__ import annotations

from typing import Optional, Union

from pytoniq_core import Address, Cell, Slice, TlbScheme, begin_cell


class VanityData(TlbScheme):

    def __init__(
            self,
            owner_address: Optional[Union[Address, str]] = None,
            salt: Optional[str] = None,
    ) -> None:
        if isinstance(owner_address, str):
            owner_address = Address(owner_address)

        self.owner_address = owner_address
        if salt is None:
            raise ValueError("Salt is required")
        self.salt = salt

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(0, 5)
            .store_address(self.owner_address)
            .store_bytes(bytes.fromhex(self.salt))
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> VanityData:
        raise NotImplementedError
