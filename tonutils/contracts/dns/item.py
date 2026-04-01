import typing as t

from ton_core import (
    Address,
    ContractVersion,
    DNSRecords,
    OnchainContent,
    TONDNSAuction,
    TONDNSItemData,
)

from tonutils.contracts.base import BaseContract
from tonutils.contracts.dns.methods import (
    DNSResolveGetMethod,
    GetAuctionInfoGetMethod,
    GetDomainGetMethod,
    GetLastFillUpTimeGetMethod,
)
from tonutils.contracts.nft.methods import GetEditorGetMethod, GetNFTDataGetMethod


class TONDNSItem(
    BaseContract[TONDNSItemData],
    GetNFTDataGetMethod,
    GetEditorGetMethod,
    GetDomainGetMethod,
    GetAuctionInfoGetMethod,
    GetLastFillUpTimeGetMethod,
    DNSResolveGetMethod,
):
    """TON DNS domain item (TEP-81)."""

    _data_model = TONDNSItemData
    VERSION = ContractVersion.TONDNSItem

    @property
    def index(self) -> int:
        """Item index in the collection."""
        return self.state_data.index

    @property
    def owner_address(self) -> Address:
        """Current domain owner address."""
        return t.cast("Address", self.state_data.owner_address)

    @property
    def collection_address(self) -> Address:
        """Parent DNS collection address."""
        return t.cast("Address", self.state_data.collection_address)

    @property
    def content(self) -> OnchainContent:
        """On-chain DNS records and metadata."""
        return self.state_data.content

    @property
    def metadata(self) -> dict[str | int, t.Any]:
        """Raw metadata dictionary from content."""
        return self.state_data.content.metadata

    @property
    def dns_records(self) -> dict[str | int, t.Any]:
        """Parsed DNS records from metadata."""
        return DNSRecords(self.state_data.content.metadata).records

    @property
    def domain(self) -> str:
        """Human-readable domain name."""
        return self.state_data.domain

    @property
    def auction(self) -> TONDNSAuction | None:
        """Active auction data, or ``None``."""
        return self.state_data.auction

    @property
    def last_fill_up_time(self) -> int:
        """Last renewal unix timestamp."""
        return self.state_data.last_fill_up_time
