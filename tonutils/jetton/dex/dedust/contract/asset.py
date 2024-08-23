from __future__ import annotations

from enum import Enum
from typing import Union

from pytoniq_core import Address, Slice, begin_cell

from ..exceptions import AssetError


class AssetType(Enum):
    NATIVE = 0
    JETTON = 1


class Asset:
    def __init__(
            self,
            asset_type: AssetType,
            address: Union[Address, str, None] = None
    ):
        self.asset_type = asset_type

        if isinstance(address, str):
            address = Address(address)

        self.address = address

    @staticmethod
    def native() -> Asset:
        return Asset(AssetType.NATIVE)

    @staticmethod
    def jetton(minter: Union[Address, str]) -> Asset:
        return Asset(AssetType.JETTON, minter)

    def to_slice(self) -> Slice:
        if self.asset_type == AssetType.NATIVE:
            return (
                begin_cell()
                .store_uint(0, 4)
                .end_cell()
                .begin_parse()
            )

        elif self.asset_type == AssetType.JETTON:
            return (
                begin_cell()
                .store_uint(AssetType.JETTON.value, 4)
                .store_int(self.address.wc, 8)
                .store_bytes(self.address.hash_part)
                .end_cell()
                .begin_parse()
            )

        else:
            raise AssetError("Asset is not supported.")

    def to_boc(self) -> bytes:
        if self.asset_type == AssetType.NATIVE:
            return (
                begin_cell()
                .store_uint(0, 4)
                .end_cell()
            ).to_boc()

        elif self.asset_type == AssetType.JETTON:
            return (
                begin_cell()
                .store_uint(AssetType.JETTON.value, 4)
                .store_int(self.address.wc, 8)
                .store_bytes(self.address.hash_part)
                .end_cell()
            ).to_boc()
        else:
            raise AssetError("Asset is not supported.")
