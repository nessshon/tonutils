from __future__ import annotations

from typing import Optional

from pytoniq_core import Cell, Slice, TlbScheme, begin_cell

from tonutils.utils import serialize_onchain_dict


class JettonOffchainContent(TlbScheme):

    def __init__(self, uri: str) -> None:
        self.uri = uri

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(0x01, 8)
            .store_snake_string(self.uri)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> JettonOffchainContent:
        raise NotImplementedError


class JettonOnchainContent(TlbScheme):

    def __init__(
            self,
            name: str,
            symbol: str,
            decimals: int,
            image: Optional[str] = None,
            image_data: Optional[bytes] = None,
            description: Optional[str] = None,
            amount_style: Optional[str] = None,
            **kwargs,
    ) -> None:
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
        self.image = image
        self.image_data = image_data
        self.description = description
        self.amount_style = amount_style

        for key, val in kwargs.items():
            setattr(self, key, val)

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_uint(0x00, 8)
            .store_dict(serialize_onchain_dict(self.__dict__))
            .end_cell()
        )

    @classmethod
    def deserialize(cls, sell_slice: Slice) -> JettonOnchainContent:
        raise NotImplementedError


class JettonStablecoinContent(TlbScheme):

    def __init__(self, uri: str) -> None:
        self.uri = uri

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_snake_string(self.uri)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, sell_slice: Slice) -> JettonStablecoinContent:
        raise NotImplementedError
