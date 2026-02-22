import typing as t

from pytoniq_core import Address, Cell, StateInit, begin_cell

from tonutils.contracts.base import BaseContract
from tonutils.contracts.dns.methods import DNSResolveGetMethod
from tonutils.contracts.dns.tlb import TONDNSCollectionData
from tonutils.contracts.nft.methods import (
    GetCollectionDataGetMethod,
    GetNFTAddressByIndexGetMethod,
    GetNFTContentGetMethod,
)
from tonutils.contracts.nft.tlb import OffchainContent
from tonutils.contracts.versions import ContractVersion
from tonutils.types import WorkchainID, AddressLike
from tonutils.utils import to_cell, string_hash


class TONDNSCollection(
    BaseContract[TONDNSCollectionData],
    GetCollectionDataGetMethod,
    GetNFTContentGetMethod,
    GetNFTAddressByIndexGetMethod,
    DNSResolveGetMethod,
):
    """TON DNS root collection."""

    _data_model = TONDNSCollectionData
    VERSION = ContractVersion.TONDNSCollection

    @property
    def owner_address(self) -> t.Optional[Address]:
        """Always `None` for DNS collections."""
        return None

    @property
    def next_item_index(self) -> int:
        """Always -1 (DNS uses domain hash as index)."""
        return -1

    @property
    def content(self) -> OffchainContent:
        """Off-chain collection content metadata."""
        return self.state_data.content

    @property
    def nft_item_code(self) -> Cell:
        """Code `Cell` for DNS domain items."""
        return self.state_data.nft_item_code

    @classmethod
    def calculate_nft_item_address(
        cls,
        index_or_domain: t.Union[str, int],
        nft_item_code: t.Union[Cell, str],
        collection_address: AddressLike,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        """Calculate DNS domain item address.

        :param index_or_domain: Domain name string or numeric hash.
        :param nft_item_code: Item contract code (`Cell` or hex string).
        :param collection_address: DNS collection address.
        :param workchain: Target workchain.
        :return: Calculated domain item address.
        """
        index = (
            index_or_domain
            if isinstance(index_or_domain, int)
            else string_hash(index_or_domain)
        )
        code = to_cell(nft_item_code)
        data = begin_cell()
        data.store_uint(index, 256)
        data.store_address(collection_address)
        state_init = StateInit(code=code, data=data.end_cell())
        return Address((workchain.value, state_init.serialize().hash))
