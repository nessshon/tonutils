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
    _data_model = TeleCollectionData

    @property
    def owner_address(self) -> t.Optional[Address]:
        return None

    @property
    def next_item_index(self) -> int:
        return -1

    @property
    def content(self) -> OffchainContent:
        return self.state_data.content

    @property
    def nft_item_code(self) -> Cell:
        return self.state_data.item_code

    @property
    def owner_key(self) -> PublicKey:
        return self.state_data.owner_key

    @property
    def subwallet_id(self) -> int:
        return self.state_data.subwallet_id

    @classmethod
    def calculate_nft_item_address(
        cls,
        index: int,
        nft_item_code: t.Union[Cell, str],
        collection_address: AddressLike,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
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
    VERSION = ContractVersion.TelegramUsernamesCollection

    @property
    def full_domain(self) -> str:
        return self.state_data.full_domain


class TelegramGiftsCollection(BaseTeleCollection):
    VERSION = ContractVersion.TelegramGiftsCollection
