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
    """Base implementation for NFT collection contracts."""

    _data_model = NFTCollectionData
    """TlbScheme class for deserializing collection state data."""

    @property
    def owner_address(self) -> t.Optional[Address]:
        """
        Owner address of this collection.

        :return: Collection owner's wallet address or None if no owner
        """
        return self.state_data.owner_address

    @property
    def next_item_index(self) -> int:
        """
        Next item index to be minted in this collection.

        :return: Next available item index
        """
        return self.state_data.next_item_index

    @property
    def content(self) -> NFTCollectionContent:
        """
        Collection content metadata.

        :return: Collection content with common metadata and base URI
        """
        return self.state_data.content

    @property
    def nft_item_code(self) -> Cell:
        """
        Code cell for NFT items in this collection.

        :return: Item contract code used for all items
        """
        return self.state_data.nft_item_code

    @classmethod
    def calculate_nft_item_address(
        cls,
        index: int,
        nft_item_code: t.Union[Cell, str],
        collection_address: AddressLike,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        """
        Calculate NFT item address by index.

        :param index: Numerical index of the item
        :param nft_item_code: Item contract code (Cell or hex string)
        :param collection_address: Collection contract address
        :param workchain: Target workchain (default: BASECHAIN)
        :return: Calculated item address
        """
        code = to_cell(nft_item_code)
        data = begin_cell()
        data.store_uint(index, 64)
        data.store_address(collection_address)
        state_init = StateInit(code=code, data=data.end_cell())
        return Address((workchain.value, state_init.serialize().hash))


class NFTCollectionStandard(BaseNFTCollection):
    """Standard NFT collection contract."""

    VERSION = ContractVersion.NFTCollectionStandard
    """Contract version identifier."""


class NFTCollectionEditable(BaseNFTCollection):
    """Editable NFT collection contract."""

    VERSION = ContractVersion.NFTCollectionEditable
    """Contract version identifier."""
