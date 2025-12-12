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
    """Base implementation for Telegram NFT collections (Usernames and Gifts)."""

    _data_model = TeleCollectionData
    """TlbScheme class for deserializing collection state data."""

    @property
    def owner_address(self) -> t.Optional[Address]:
        """
        Owner address of this collection.

        :return: Always None for Telegram collections (no single owner)
        """
        return None

    @property
    def next_item_index(self) -> int:
        """
        Next item index to be minted.

        :return: Always -1 for Telegram collections (pre-minted items)
        """
        return -1

    @property
    def content(self) -> OffchainContent:
        """
        Off-chain collection content metadata.

        :return: Collection content with URI and metadata
        """
        return self.state_data.content

    @property
    def nft_item_code(self) -> Cell:
        """
        Code cell for NFT items in this collection.

        :return: Item contract code
        """
        return self.state_data.item_code

    @property
    def owner_key(self) -> PublicKey:
        """
        Public key of the collection owner.

        :return: Ed25519 public key instance
        """
        return self.state_data.owner_key

    @property
    def subwallet_id(self) -> int:
        """
        Subwallet ID for collection operations.

        :return: Subwallet identifier
        """
        return self.state_data.subwallet_id

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
        item_config = TeleItemConfig(index, collection_address)
        item_data = TeleItemData(item_config, state=None)
        state_init = StateInit(code=code, data=item_data.serialize())
        return Address((workchain.value, state_init.serialize().hash))


class TelegramUsernamesCollection(
    BaseTeleCollection,
    GetFullDomainGetMethod,
    DNSResolveGetMethod,
):
    """Telegram Usernames NFT collection contract."""

    VERSION = ContractVersion.TelegramUsernamesCollection
    """Contract version identifier."""

    @property
    def full_domain(self) -> str:
        """
        Full domain name for this collection.

        :return: Collection domain (e.g., "t.me")
        """
        return self.state_data.full_domain


class TelegramGiftsCollection(BaseTeleCollection):
    """Telegram Gifts NFT collection contract."""

    VERSION = ContractVersion.TelegramGiftsCollection
    """Contract version identifier."""
