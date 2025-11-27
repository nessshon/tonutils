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
    _data_model = TONDNSItemData
    VERSION = ContractVersion.TONDNSItem

    @property
    def index(self) -> int:
        return self.state_data.index

    @property
    def owner_address(self) -> Address:
        return self.state_data.owner_address

    @property
    def collection_address(self) -> Address:
        return self.state_data.collection_address

    @property
    def content(self) -> OnchainContent:
        return self.state_data.content

    @property
    def metadata(self) -> t.Dict[t.Union[str, int], t.Any]:
        return self.state_data.content.metadata

    @property
    def dns_records(self) -> t.Dict[t.Union[str, int], t.Any]:
        return DNSRecords(self.state_data.content.metadata).records

    @property
    def domain(self) -> str:
        return self.state_data.domain

    @property
    def auction(self) -> t.Optional[TONDNSAuction]:
        return self.state_data.auction

    @property
    def last_fill_up_time(self) -> int:
        return self.state_data.last_fill_up_time
