import typing as t

from pytoniq_core import Address, Cell, StateInit, begin_cell

from tonutils.contracts.base import BaseContract
from tonutils.contracts.nft.methods import (
    GetCollectionDataGetMethod,
    GetNFTContentGetMethod,
    GetNFTAddressByIndexGetMethod,
    RoyaltyParamsGetMethod,
)
from tonutils.contracts.nft.tlb import (
    NFTCollectionData,
    NFTCollectionContent,
)
from tonutils.contracts.versions import ContractVersion
from tonutils.types import AddressLike, WorkchainID
from tonutils.utils import to_cell


class BaseNFTCollection(
    BaseContract[NFTCollectionData],
    GetCollectionDataGetMethod,
    GetNFTContentGetMethod,
    GetNFTAddressByIndexGetMethod,
    RoyaltyParamsGetMethod,
):
    _data_model = NFTCollectionData

    @property
    def owner_address(self) -> t.Optional[Address]:
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


class NFTCollectionStandard(BaseNFTCollection):
    VERSION = ContractVersion.NFTCollectionStandard


class NFTCollectionEditable(BaseNFTCollection):
    VERSION = ContractVersion.NFTCollectionEditable
