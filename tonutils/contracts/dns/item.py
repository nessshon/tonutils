import typing as t

from pytoniq_core import Address

from tonutils.contracts.base import BaseContract
from tonutils.contracts.dns.methods import (
    GetDomainGetMethod,
    GetAuctionInfoGetMethod,
    GetLastFillUpTimeGetMethod,
    DNSResolveGetMethod,
)
from tonutils.contracts.dns.tlb import TONDNSItemData, TONDNSAuction, DNSRecords
from tonutils.contracts.nft.methods import GetNFTDataGetMethod, GetEditorGetMethod
from tonutils.contracts.nft.tlb import OnchainContent
from tonutils.contracts.versions import ContractVersion


class TONDNSItem(
    BaseContract[TONDNSItemData],
    GetNFTDataGetMethod,
    GetEditorGetMethod,
    GetDomainGetMethod,
    GetAuctionInfoGetMethod,
    GetLastFillUpTimeGetMethod,
    DNSResolveGetMethod,
):
    """TON DNS domain item contract."""

    _data_model = TONDNSItemData
    """TlbScheme class for deserializing DNS item state data."""

    VERSION = ContractVersion.TONDNSItem
    """Contract version identifier."""

    @property
    def index(self) -> int:
        """
        Numerical index of this DNS item in the collection.

        :return: Item index
        """
        return self.state_data.index

    @property
    def owner_address(self) -> Address:
        """
        Current owner address of this DNS domain.

        :return: Owner's wallet address
        """
        return self.state_data.owner_address

    @property
    def collection_address(self) -> Address:
        """
        DNS collection address this item belongs to.

        :return: Parent collection address
        """
        return self.state_data.collection_address

    @property
    def content(self) -> OnchainContent:
        """
        DNS item onchain content metadata.

        :return: Onchain content with metadata
        """
        return self.state_data.content

    @property
    def metadata(self) -> t.Dict[t.Union[str, int], t.Any]:
        """
        Raw metadata dictionary from content.

        :return: Metadata key-value pairs
        """
        return self.state_data.content.metadata

    @property
    def dns_records(self) -> t.Dict[t.Union[str, int], t.Any]:
        """
        Parsed DNS records from metadata.

        :return: DNS records mapping domain names to addresses
        """
        return DNSRecords(self.state_data.content.metadata).records

    @property
    def domain(self) -> str:
        """
        Human-readable domain name (e.g., "example.ton").

        :return: Domain name string
        """
        return self.state_data.domain

    @property
    def auction(self) -> t.Optional[TONDNSAuction]:
        """
        Active auction information for this domain.

        :return: Auction data or None if no active auction
        """
        return self.state_data.auction

    @property
    def last_fill_up_time(self) -> int:
        """
        Unix timestamp of last domain renewal/fill-up.

        :return: Last fill-up timestamp
        """
        return self.state_data.last_fill_up_time
