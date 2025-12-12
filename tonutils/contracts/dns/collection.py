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
    """TON DNS root collection contract."""

    _data_model = TONDNSCollectionData
    """TlbScheme class for deserializing DNS collection state data."""

    VERSION = ContractVersion.TONDNSCollection
    """Contract version identifier."""

    @property
    def owner_address(self) -> t.Optional[Address]:
        """
        Owner address of this DNS collection.

        :return: Always None (DNS collection has no single owner)
        """
        return None

    @property
    def next_item_index(self) -> int:
        """
        Next item index in this DNS collection.

        :return: Always -1 (DNS uses domain hash as index, not sequential)
        """
        return -1

    @property
    def content(self) -> OffchainContent:
        """
        DNS collection offchain content metadata.

        :return: Collection content with metadata URI
        """
        return self.state_data.content

    @property
    def nft_item_code(self) -> Cell:
        """
        Code cell for DNS domain items in this collection.

        :return: Domain item contract code used for all domains
        """
        return self.state_data.nft_item_code

    @classmethod
    def calculate_nft_item_address(
        cls,
        index_or_domain: t.Union[str, int],
        nft_item_code: t.Union[Cell, str],
        collection_address: AddressLike,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        """
        Calculate DNS domain item address by index or domain name.

        :param index_or_domain: Domain name string (e.g., "test.ton") or numeric hash
        :param nft_item_code: Domain item contract code (Cell or hex string)
        :param collection_address: DNS collection contract address
        :param workchain: Target workchain (default: BASECHAIN)
        :return: Calculated domain item address
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
