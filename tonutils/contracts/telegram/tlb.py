from __future__ import annotations

import typing as t

from pytoniq_core import Builder, Cell, Slice, TlbScheme, begin_cell

from tonutils.contracts.dns.tlb import DNSRecords
from tonutils.contracts.nft.tlb import RoyaltyParams, OffchainContent
from tonutils.contracts.opcodes import OpCode
from tonutils.types import AddressLike, PublicKey
from tonutils.utils import decode_dns_name


def _store_text(b: Builder, text: str) -> Builder:
    """Store length-prefixed text into a `Builder`.

    :param b: Target builder.
    :param text: Text string to store.
    :return: The same builder.
    """
    bit_len = begin_cell().store_snake_string(text)
    bytes_len, remainder = divmod(bit_len.remaining_bits, 8)
    if remainder != 0:
        raise ValueError("Text length must be a multiple of 8 bits.")
    return b.store_uint(bytes_len, 8).store_slice(text)


def _load_text(cs: Slice) -> bytes:
    """Load length-prefixed text from a `Slice`.

    :param cs: Source slice.
    :return: Text bytes.
    """
    length_bytes = cs.load_uint(8)
    text = cs.load_bits(length_bytes * 8)
    return text.tobytes()


class TeleItemAuctionState(TlbScheme):
    """Current state of a Telegram item auction."""

    def __init__(
        self,
        min_bid: int,
        end_time: int,
        last_bid: t.Optional[Cell] = None,
    ) -> None:
        """
        :param min_bid: Minimum bid in nanotons.
        :param end_time: Auction end unix timestamp.
        :param last_bid: Last bid info cell, or `None`.
        """
        self.last_bid = last_bid
        self.min_bid = min_bid
        self.end_time = end_time

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `last_bid:^Cell min_bid:coins end_time:uint32`
        """
        cell = begin_cell()
        cell.store_maybe_ref(self.last_bid)
        cell.store_coins(self.min_bid)
        cell.store_uint(self.end_time, 32)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemAuctionState:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            last_bid=cs.load_maybe_ref(),
            min_bid=cs.load_coins(),
            end_time=cs.load_uint(32),
        )


class TeleItemAuctionConfig(TlbScheme):
    """Configuration parameters for a Telegram item auction."""

    def __init__(
        self,
        beneficiary_address: AddressLike,
        initial_min_bid: int,
        max_bid: int,
        min_bid_step: int,
        min_extend_time: int,
        duration: int,
    ) -> None:
        """
        :param beneficiary_address: Address to receive proceeds.
        :param initial_min_bid: Starting minimum bid in nanotons.
        :param max_bid: Maximum bid in nanotons.
        :param min_bid_step: Minimum bid increment (0–255).
        :param min_extend_time: Seconds to extend on late bids.
        :param duration: Total auction duration in seconds.
        """
        self.beneficiary_address = beneficiary_address
        self.initial_min_bid = initial_min_bid
        self.max_bid = max_bid
        self.min_bid_step = min_bid_step
        self.min_extend_time = min_extend_time
        self.duration = duration

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `beneficiary:address initial_min_bid:coins max_bid:coins
        min_bid_step:uint8 min_extend_time:uint32 duration:uint32`
        """
        cell = begin_cell()
        cell.store_address(self.beneficiary_address)
        cell.store_coins(self.initial_min_bid)
        cell.store_coins(self.max_bid)
        cell.store_uint(self.min_bid_step, 8)
        cell.store_uint(self.min_extend_time, 32)
        cell.store_uint(self.duration, 32)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemAuctionConfig:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            beneficiary_address=cs.load_address(),
            initial_min_bid=cs.load_coins(),
            max_bid=cs.load_coins(),
            min_bid_step=cs.load_uint(8),
            min_extend_time=cs.load_uint(32),
            duration=cs.load_uint(32),
        )


class TeleItemAuction(TlbScheme):
    """Complete auction data combining state and configuration."""

    def __init__(
        self,
        state: TeleItemAuctionState,
        config: TeleItemAuctionConfig,
    ) -> None:
        """
        :param state: Current auction state.
        :param config: Auction configuration.
        """
        self.state = state
        self.config = config

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `state:^Cell config:^Cell`
        """
        cell = begin_cell()
        cell.store_ref(self.state.serialize())
        cell.store_ref(self.config.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemAuction:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            state=TeleItemAuctionState.deserialize(cs.load_ref().begin_parse()),
            config=TeleItemAuctionConfig.deserialize(cs.load_ref().begin_parse()),
        )


class TeleItemConfig(TlbScheme):
    """Static configuration for a Telegram item NFT."""

    def __init__(
        self,
        item_index: int,
        collection_address: AddressLike,
    ) -> None:
        """
        :param item_index: Index within the collection.
        :param collection_address: Parent collection address.
        """
        self.item_index = item_index
        self.collection_address = collection_address

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `item_index:uint256 collection_address:address`
        """
        cell = begin_cell()
        cell.store_uint(self.item_index, 256)
        cell.store_address(self.collection_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemConfig:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            item_index=cs.load_uint(256),
            collection_address=cs.load_address(),
        )


class TeleItemTokenInfo(TlbScheme):
    """Token information for a Telegram item."""

    def __init__(
        self,
        name: str,
        domain: str,
    ) -> None:
        """
        :param name: Username or gift name.
        :param domain: Associated domain (e.g. "t.me").
        """
        self.name = name
        self.domain = domain

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `name:text domain:text`
        """
        cell = begin_cell()
        _store_text(cell, self.name)
        _store_text(cell, self.domain)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemTokenInfo:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            name=decode_dns_name(_load_text(cs)),
            domain=decode_dns_name(_load_text(cs)),
        )


class TeleItemContent(TlbScheme):
    """Complete content data for a Telegram item NFT."""

    def __init__(
        self,
        nft_content: OffchainContent,
        dns: DNSRecords,
        token_info: TeleItemTokenInfo,
    ) -> None:
        """
        :param nft_content: Off-chain NFT metadata.
        :param dns: DNS records for the username/domain.
        :param token_info: Token name and domain information.
        """
        self.nft_content = nft_content
        self.dns = dns
        self.token_info = token_info

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `nft_content:^Cell dns:dict token_info:^Cell`
        """
        cell = begin_cell()
        cell.store_ref(self.nft_content.serialize(True))
        cell.store_dict(self.dns.serialize(False).begin_parse().load_maybe_ref())
        cell.store_ref(self.token_info.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemContent:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            nft_content=OffchainContent.deserialize(cs.load_ref().begin_parse(), True),
            dns=DNSRecords.deserialize(cs, False),
            token_info=TeleItemTokenInfo.deserialize(cs.load_ref().begin_parse()),
        )


class TeleItemState(TlbScheme):
    """Mutable state of a Telegram item NFT."""

    def __init__(
        self,
        owner_address: AddressLike,
        content: TeleItemContent,
        royalty_params: RoyaltyParams,
        auction: t.Optional[TeleItemAuction] = None,
    ) -> None:
        """
        :param owner_address: Current owner address.
        :param content: Item content data.
        :param royalty_params: Royalty configuration.
        :param auction: Active auction data, or `None`.
        """
        self.owner_address = owner_address
        self.content = content
        self.auction = auction
        self.royalty_params = royalty_params

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `owner:address content:^Cell auction:^Cell royalty_params:^Cell`
        """
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_ref(self.content.serialize())
        cell.store_maybe_ref(self.auction.serialize() if self.auction else None)
        cell.store_ref(self.royalty_params.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemState:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        cs.preload_ref()
        return cls(
            owner_address=cs.load_address(),
            content=TeleItemContent.deserialize(cs.load_ref().begin_parse()),
            auction=(
                TeleItemAuction.deserialize(cs.load_ref().begin_parse())
                if cs.load_bit()
                else None
            ),
            royalty_params=RoyaltyParams.deserialize(cs.load_ref().begin_parse()),
        )


class TeleItemData(TlbScheme):
    """Complete on-chain data for a Telegram item NFT."""

    def __init__(
        self,
        config: TeleItemConfig,
        state: t.Optional[TeleItemState] = None,
    ) -> None:
        """
        :param config: Static item configuration.
        :param state: Mutable item state, or `None`.
        """
        self.config = config
        self.state = state

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `config:^Cell state:^Cell`
        """
        cell = begin_cell()
        cell.store_ref(self.config.serialize())
        cell.store_maybe_ref(self.state.serialize() if self.state else None)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemData:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            config=TeleItemConfig.deserialize(cs.load_ref().begin_parse()),
            state=(
                TeleItemState.deserialize(cs.load_ref().begin_parse())
                if cs.load_bit()
                else None
            ),
        )


class TeleCollectionData(TlbScheme):
    """On-chain data for a Telegram collection NFT."""

    def __init__(
        self,
        touched: bool,
        subwallet_id: int,
        owner_key: PublicKey,
        content: OffchainContent,
        item_code: Cell,
        full_domain: str,
        royalty_params: RoyaltyParams,
    ) -> None:
        """
        :param touched: Whether collection has been initialized.
        :param subwallet_id: Subwallet identifier.
        :param owner_key: Owner's public key.
        :param content: Off-chain collection metadata.
        :param item_code: Code cell for item contracts.
        :param full_domain: Collection domain (e.g. "t.me").
        :param royalty_params: Royalty configuration.
        """
        self.touched = touched
        self.subwallet_id = subwallet_id
        self.owner_key = owner_key
        self.content = content
        self.item_code = item_code
        self.full_domain = full_domain
        self.royalty_params = royalty_params

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `touched:bool subwallet_id:uint32 owner_key:uint256
        content:^Cell item_code:^Cell full_domain:^Cell royalty_params:^Cell`
        """
        cell = begin_cell()
        cell.store_bool(self.touched)
        cell.store_uint(self.subwallet_id, 32)
        cell.store_uint(self.owner_key.as_int, 256)
        cell.store_ref(self.content.serialize(True))
        cell.store_ref(self.item_code)
        cell.store_ref(_store_text(begin_cell(), self.full_domain).end_cell())
        cell.store_ref(self.royalty_params.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleCollectionData:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            touched=cs.load_bool(),
            subwallet_id=cs.load_uint(32),
            owner_key=PublicKey(cs.load_uint(256)),
            content=OffchainContent.deserialize(cs.load_ref().begin_parse(), True),
            item_code=cs.load_ref(),
            full_domain=decode_dns_name(_load_text(cs.load_ref().begin_parse())),
            royalty_params=RoyaltyParams.deserialize(cs.load_ref().begin_parse()),
        )


class TeleItemStartAuctionBody(TlbScheme):
    """Message body for starting an auction on a Telegram item."""

    def __init__(
        self,
        auction_config: TeleItemAuctionConfig,
        query_id: int = 0,
    ) -> None:
        """
        :param auction_config: Auction configuration.
        :param query_id: Query identifier.
        """
        self.query_id = query_id
        self.auction_config = auction_config

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 auction_config:^Cell`
        """
        cell = begin_cell()
        cell.store_uint(OpCode.TELEITEM_START_AUCTION, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.auction_config.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemStartAuctionBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class TeleItemCancelAuctionBody(TlbScheme):
    """Message body for canceling an auction on a Telegram item."""

    def __init__(self, query_id: int = 0) -> None:
        """
        :param query_id: Query identifier.
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64`
        """
        cell = begin_cell()
        cell.store_uint(OpCode.TELEITEM_CANCEL_AUCTION, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemStartAuctionBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError
