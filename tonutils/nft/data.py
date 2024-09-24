from __future__ import annotations

from typing import Optional, Union

from pytoniq_core import Address, Cell, Slice, TlbScheme, begin_cell

from .content import BaseOnchainContent, BaseOffchainContent
from .royalty_params import RoyaltyParams


class CollectionData(TlbScheme):

    def __init__(
            self,
            owner_address: Optional[Union[Address, str]] = None,
            next_item_index: Optional[int] = None,
            content: Optional[Union[BaseOnchainContent, BaseOffchainContent, Cell]] = None,
            royalty_params: Optional[Union[RoyaltyParams, Cell]] = None,
            nft_item_code: Optional[Union[Cell, str]] = None,
    ) -> None:
        self.next_item_index = next_item_index

        if isinstance(owner_address, str):
            owner_address = Address(owner_address)
        self.owner_address = owner_address

        if isinstance(content, (BaseOnchainContent, BaseOffchainContent)):
            content = content.serialize()
        self.content = content

        if isinstance(nft_item_code, str):
            nft_item_code = Cell.one_from_boc(nft_item_code)
        self.nft_item_code = nft_item_code

        if isinstance(royalty_params, RoyaltyParams):
            royalty_params = royalty_params.serialize()
        self.royalty_params = royalty_params

    def serialize(self) -> Cell:
        return (
            begin_cell()
            .store_address(self.owner_address)
            .store_uint(self.next_item_index, 64)
            .store_ref(self.content)
            .store_ref(self.nft_item_code)
            .store_ref(self.royalty_params)
            .end_cell()
        )

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> CollectionData:
        raise NotImplementedError


class NFTData(TlbScheme):

    def __init__(
            self,
            index: Optional[int] = None,
            collection_address: Optional[Union[Address, str]] = None,
            owner_address: Optional[Union[Address, str]] = None,
            content: Optional[Union[BaseOnchainContent, BaseOffchainContent, Cell]] = None,
    ) -> None:
        self.index = index

        if isinstance(collection_address, str):
            collection_address = Address(collection_address)
        self.collection_address = collection_address

        if isinstance(owner_address, str):
            owner_address = Address(owner_address)
        self.owner_address = owner_address

        if isinstance(content, (BaseOffchainContent, BaseOnchainContent)):
            content = content.serialize()
        self.content = content

    def serialize(self) -> Cell:
        cell = (
            begin_cell()
            .store_uint(self.index, 64)
            .store_address(self.collection_address)
        )

        if self.owner_address is not None:
            cell = cell.store_address(self.owner_address)

        if self.content is not None:
            cell = cell.store_ref(self.content)

        return cell.end_cell()

    @classmethod
    def deserialize(cls, cell_slice: Slice) -> NFTData:
        raise NotImplementedError
