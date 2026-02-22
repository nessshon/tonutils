import typing as t

from pytoniq_core import Cell, Address, StateInit

from tonutils.contracts.base import BaseContract
from tonutils.contracts.dns.methods import DNSResolveGetMethod
from tonutils.contracts.nft.methods import (
    GetCollectionDataGetMethod,
    GetNFTContentGetMethod,
    GetNFTAddressByIndexGetMethod,
)
from tonutils.contracts.nft.tlb import OffchainContent
from tonutils.contracts.telegram.methods import GetFullDomainGetMethod
from tonutils.contracts.telegram.tlb import (
    TeleCollectionData,
    TeleItemConfig,
    TeleItemData,
)
from tonutils.contracts.versions import ContractVersion
from tonutils.types import AddressLike, PublicKey, WorkchainID
from tonutils.utils import to_cell


class BaseTeleCollection(
    BaseContract[TeleCollectionData],
    GetCollectionDataGetMethod,
    GetNFTAddressByIndexGetMethod,
    GetNFTContentGetMethod,
):
    """Base implementation for Telegram NFT collections."""

    _data_model = TeleCollectionData

    @property
    def owner_address(self) -> t.Optional[Address]:
        """Always `None` for Telegram collections."""
        return None

    @property
    def next_item_index(self) -> int:
        """Always -1 for Telegram collections."""
        return -1

    @property
    def content(self) -> OffchainContent:
        """Off-chain collection content metadata."""
        return self.state_data.content

    @property
    def nft_item_code(self) -> Cell:
        """Code `Cell` for NFT items in this collection."""
        return self.state_data.item_code

    @property
    def owner_key(self) -> PublicKey:
        """Ed25519 public key of the collection owner."""
        return self.state_data.owner_key

    @property
    def subwallet_id(self) -> int:
        """Subwallet identifier for collection operations."""
        return self.state_data.subwallet_id

    @classmethod
    def calculate_nft_item_address(
        cls,
        index: int,
        nft_item_code: t.Union[Cell, str],
        collection_address: AddressLike,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        """Calculate NFT item address by index.

        :param index: Item index in the collection.
        :param nft_item_code: Item contract code (`Cell` or hex string).
        :param collection_address: Parent collection address.
        :param workchain: Target workchain.
        :return: Calculated item address.
        """
        code = to_cell(nft_item_code)
        item_config = TeleItemConfig(index, collection_address)
        item_data = TeleItemData(item_config, state=None)
        state_init = StateInit(code=code, data=item_data.serialize())
        return Address((workchain.value, state_init.serialize().hash))


class TelegramUsernamesCollection(
    BaseTeleCollection,
    GetFullDomainGetMethod,
    DNSResolveGetMethod,
):
    """Telegram Usernames NFT collection."""

    VERSION = ContractVersion.TelegramUsernamesCollection

    @property
    def full_domain(self) -> str:
        """Full domain name for this collection."""
        return self.state_data.full_domain


class TelegramGiftsCollection(BaseTeleCollection):
    """Telegram Gifts NFT collection."""

    VERSION = ContractVersion.TelegramGiftsCollection
