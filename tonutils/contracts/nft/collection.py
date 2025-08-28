import typing as t

from pytoniq_core import (
    Address,
    Cell,
    Slice,
    StateInit,
    begin_cell,
)

from .get_methods import NFTCollectionGetMethods
from ..base import BaseContract
from ...types import (
    AddressLike,
    NFTCollectionContent,
    NFTCollectionData,
    NFTCollectionVersion,
    NFTItemVersion,
    MetadataPrefix,
    OnchainContent,
    OffchainContent,
    RoyaltyParams,
    WorkchainID,
)
from ...utils import to_cell


class BaseNFTCollection(BaseContract[NFTCollectionData]):
    _data_model = NFTCollectionData
    NFT_ITEM_VERSION: NFTItemVersion

    @property
    def owner_address(self) -> Address:
        return self.state_data.owner_address

    @property
    def next_item_index(self) -> int:
        return self.state_data.next_item_index

    @property
    def content(self) -> NFTCollectionContent:
        return self.state_data.content

    @property
    def nft_item_code(self) -> Cell:
        return self.state_data.nft_item_code

    @classmethod
    def calculate_nft_item_address(
        cls,
        index: int,
        nft_item_code: t.Union[Cell, str],
        collection_address: AddressLike,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        code = to_cell(nft_item_code)
        data = begin_cell()
        data.store_uint(index, 64)
        data.store_address(collection_address)
        state_init = StateInit(code=code, data=data.end_cell())
        return Address((workchain.value, state_init.serialize().hash))

    async def get_collection_data(self) -> t.Tuple[
        int,
        t.Union[OnchainContent, OffchainContent],
        t.Optional[Address],
    ]:
        method_result = await NFTCollectionGetMethods.get_collection_data(
            client=self.client,
            address=self.address,
        )
        content_cs: Slice = method_result[1].begin_parse()
        return (
            method_result[0],
            (
                OnchainContent.deserialize(content_cs, False)
                if content_cs.load_uint(8) == MetadataPrefix.ONCHAIN
                else OffchainContent.deserialize(content_cs, False)
            ),
            method_result[2],
        )

    async def get_nft_content(
        self,
        index: int,
        individual_nft_content: Cell,
    ) -> OffchainContent:
        cell = await NFTCollectionGetMethods.get_nft_content(
            client=self.client,
            address=self.address,
            index=index,
            individual_nft_content=individual_nft_content,
        )
        return OffchainContent.deserialize(cell.begin_parse(), True)

    async def get_nft_address_by_index(self, index: int) -> Address:
        return await NFTCollectionGetMethods.get_nft_address_by_index(
            client=self.client,
            address=self.address,
            index=index,
        )

    async def royalty_params(self) -> RoyaltyParams:
        royalty, denominator, address = await NFTCollectionGetMethods.royalty_params(
            client=self.client,
            address=self.address,
        )
        return RoyaltyParams(royalty, denominator, address)


class NFTCollectionStandard(BaseNFTCollection):
    VERSION = NFTCollectionVersion.NFTCollectionStandard


class NFTCollectionEditable(BaseNFTCollection):
    VERSION = NFTCollectionVersion.NFTCollectionEditable
