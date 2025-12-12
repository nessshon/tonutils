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
    """Base implementation for Telegram NFT items (Usernames and Gifts)."""

    _data_model = TeleItemData
    """TlbScheme class for deserializing item state data."""

    @property
    def state(self) -> TeleItemState:
        """
        Current state of the Telegram item.

        :return: Item state containing owner, content, and auction data
        """
        if self.state_data.state is None:
            raise ValueError("Item has no state — state is undefined.")
        return t.cast(TeleItemState, self.state_data.state)

    @property
    def index(self) -> int:
        """
        Numerical index of this item in the collection.

        :return: Item index
        """
        return self.state_data.config.item_index

    @property
    def owner_address(self) -> Address:
        """
        Current owner address of this item.

        :return: Owner's wallet address
        """
        return self.state.owner_address

    @property
    def collection_address(self) -> Address:
        """
        Collection address this item belongs to.

        :return: Parent collection address
        """
        return self.state_data.config.collection_address

    @property
    def content(self) -> OffchainContent:
        """
        Off-chain NFT content metadata.

        :return: NFT content with URI and metadata
        """
        return self.state.content.nft_content

    @property
    def token_info(self) -> TeleItemTokenInfo:
        """
        Token-specific information (name, domain, etc.).

        :return: Token info containing name and domain data
        """
        return self.state.content.token_info

    @property
    def auction(self) -> t.Optional[TeleItemAuction]:
        """
        Active auction data if item is being auctioned.

        :return: Auction details or None if not in auction
        """
        return self.state.auction


class TelegramUsernameItem(
    BaseTeleItem,
    GetFullDomainGetMethod,
    DNSResolveGetMethod,
):
    """Telegram Username NFT item contract."""

    VERSION = ContractVersion.TelegramUsernameItem
    """Contract version identifier."""

    @property
    def full_domain(self) -> str:
        """
        Full domain name including subdomain and TLD.

        :return: Full domain string (e.g., "username.t.me")
        """
        if not self.state.content.token_info.domain:
            raise ValueError("Item is no dns cheap - domain is undefined.")
        return f"{self.state.content.token_info.name}.{self.state.content.token_info.domain}"

    @property
    def dns_records(self) -> t.Dict[t.Union[str, int], t.Any]:
        """
        DNS records associated with this username.

        :return: Dictionary of DNS records by category
        """
        return self.state.content.dns.records


class TelegramGiftItem(BaseTeleItem):
    """Telegram Gift NFT item contract."""

    VERSION = ContractVersion.TelegramGiftItem
    """Contract version identifier."""
