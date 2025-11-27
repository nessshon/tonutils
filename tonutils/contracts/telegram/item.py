import typing as t

from pytoniq_core import Address

from tonutils.contracts.base import BaseContract
from tonutils.contracts.dns.methods import DNSResolveGetMethod
from tonutils.contracts.nft.methods import (
    GetNFTDataGetMethod,
    RoyaltyParamsGetMethod,
)
from tonutils.contracts.nft.tlb import OffchainContent
from tonutils.contracts.telegram.methods import (
    GetTelemintAuctionConfigGetMethod,
    GetTelemintAuctionStateGetMethod,
    GetTelemintTokenNameGetMethod,
    GetFullDomainGetMethod,
)
from tonutils.contracts.telegram.tlb import (
    TeleItemAuction,
    TeleItemData,
    TeleItemTokenInfo,
    TeleItemState,
)
from tonutils.contracts.versions import ContractVersion


class BaseTeleItem(
    BaseContract[TeleItemData],
    GetNFTDataGetMethod,
    GetTelemintTokenNameGetMethod,
    GetTelemintAuctionStateGetMethod,
    GetTelemintAuctionConfigGetMethod,
    RoyaltyParamsGetMethod,
):
    _data_model = TeleItemData

    @property
    def state(self) -> TeleItemState:
        if self.state_data.state is None:
            raise ValueError("Item has no state — state is undefined.")
        return t.cast(TeleItemState, self.state_data.state)

    @property
    def index(self) -> int:
        return self.state_data.config.item_index

    @property
    def owner_address(self) -> Address:
        return self.state.owner_address

    @property
    def collection_address(self) -> Address:
        return self.state_data.config.collection_address

    @property
    def content(self) -> OffchainContent:
        return self.state.content.nft_content

    @property
    def token_info(self) -> TeleItemTokenInfo:
        return self.state.content.token_info

    @property
    def auction(self) -> t.Optional[TeleItemAuction]:
        return self.state.auction


class TelegramUsernameItem(
    BaseTeleItem,
    GetFullDomainGetMethod,
    DNSResolveGetMethod,
):
    VERSION = ContractVersion.TelegramUsernameItem

    @property
    def full_domain(self) -> str:
        if not self.state.content.token_info.domain:
            raise ValueError("Item is no dns cheap - domain is undefined.")
        return f"{self.state.content.token_info.name}.{self.state.content.token_info.domain}"

    @property
    def dns_records(self) -> t.Dict[t.Union[str, int], t.Any]:
        return self.state.content.dns.records


class TelegramGiftItem(BaseTeleItem):
    VERSION = ContractVersion.TelegramGiftItem
