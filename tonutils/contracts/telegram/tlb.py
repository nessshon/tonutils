from __future__ import annotations

import typing as t

from pytoniq_core import Builder, Cell, Slice, TlbScheme, begin_cell

from tonutils.contracts.dns.tlb import DNSRecords
from tonutils.contracts.nft.tlb import RoyaltyParams, OffchainContent
from tonutils.contracts.opcodes import OpCode
from tonutils.types import AddressLike, PublicKey
from tonutils.utils import decode_dns_name


def _store_text(b: Builder, text: str) -> Builder:
    """
    Store text with length prefix to builder.

    :param b: Cell builder to store to
    :param text: Text string to store
    :return: Builder with stored text
    """
    bit_len = begin_cell().store_snake_string(text)
    bytes_len, remainder = divmod(bit_len.remaining_bits, 8)
    if remainder != 0:
        raise ValueError("Text length must be a multiple of 8 bits.")
    return b.store_uint(bytes_len, 8).store_slice(text)


def _load_text(cs: Slice) -> bytes:
    """
    Load text with length prefix from slice.

    :param cs: Cell slice to load from
    :return: Text bytes
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
        Initialize auction state.

        :param min_bid: Minimum bid amount in nanotons
        :param end_time: Unix timestamp when auction ends
        :param last_bid: Cell containing last bid information (default: None)
        """
        self.last_bid = last_bid
        self.min_bid = min_bid
        self.end_time = end_time

    def serialize(self) -> Cell:
        """
        Serialize auction state to Cell.

        Layout: last_bid:^Cell min_bid:coins end_time:uint32

        :return: Serialized state cell
        """
        cell = begin_cell()
        cell.store_maybe_ref(self.last_bid)
        cell.store_coins(self.min_bid)
        cell.store_uint(self.end_time, 32)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemAuctionState:
        """
        Deserialize auction state from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemAuctionState instance
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
        Initialize auction configuration.

        :param beneficiary_address: Address to receive auction proceeds
        :param initial_min_bid: Starting minimum bid in nanotons
        :param max_bid: Maximum bid amount in nanotons
        :param min_bid_step: Minimum bid increment percentage (0-255)
        :param min_extend_time: Seconds to extend auction on late bids
        :param duration: Total auction duration in seconds
        """
        self.beneficiary_address = beneficiary_address
        self.initial_min_bid = initial_min_bid
        self.max_bid = max_bid
        self.min_bid_step = min_bid_step
        self.min_extend_time = min_extend_time
        self.duration = duration

    def serialize(self) -> Cell:
        """
        Serialize auction config to Cell.

        Layout: beneficiary:address initial_min_bid:coins max_bid:coins
                min_bid_step:uint8 min_extend_time:uint32 duration:uint32

        :return: Serialized config cell
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
        """
        Deserialize auction config from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemAuctionConfig instance
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
        Initialize auction data.

        :param state: Current auction state
        :param config: Auction configuration parameters
        """
        self.state = state
        self.config = config

    def serialize(self) -> Cell:
        """
        Serialize auction to Cell.

        Layout: state:^Cell config:^Cell

        :return: Serialized auction cell
        """
        cell = begin_cell()
        cell.store_ref(self.state.serialize())
        cell.store_ref(self.config.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemAuction:
        """
        Deserialize auction from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemAuction instance
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
        Initialize item configuration.

        :param item_index: Unique index within the collection
        :param collection_address: Address of parent collection contract
        """
        self.item_index = item_index
        self.collection_address = collection_address

    def serialize(self) -> Cell:
        """
        Serialize item config to Cell.

        Layout: item_index:uint256 collection_address:address

        :return: Serialized config cell
        """
        cell = begin_cell()
        cell.store_uint(self.item_index, 256)
        cell.store_address(self.collection_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemConfig:
        """
        Deserialize item config from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemConfig instance
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
        Initialize token information.

        :param name: Username or gift name
        :param domain: Associated domain (e.g., "t.me")
        """
        self.name = name
        self.domain = domain

    def serialize(self) -> Cell:
        """
        Serialize token info to Cell.

        Layout: name:text domain:text (with length prefixes)

        :return: Serialized token info cell
        """
        cell = begin_cell()
        _store_text(cell, self.name)
        _store_text(cell, self.domain)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemTokenInfo:
        """
        Deserialize token info from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemTokenInfo instance
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
        Initialize item content.

        :param nft_content: Off-chain NFT metadata (image, description, etc)
        :param dns: DNS records for the username/domain
        :param token_info: Token name and domain information
        """
        self.nft_content = nft_content
        self.dns = dns
        self.token_info = token_info

    def serialize(self) -> Cell:
        """
        Serialize item content to Cell.

        Layout: nft_content:^Cell dns:dict token_info:^Cell

        :return: Serialized content cell
        """
        cell = begin_cell()
        cell.store_ref(self.nft_content.serialize(True))
        cell.store_dict(self.dns.serialize(False).begin_parse().load_maybe_ref())
        cell.store_ref(self.token_info.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemContent:
        """
        Deserialize item content from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemContent instance
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
        Initialize item state.

        :param owner_address: Current owner address
        :param content: Item content data
        :param royalty_params: Royalty configuration for sales
        :param auction: Active auction data (None if no auction)
        """
        self.owner_address = owner_address
        self.content = content
        self.auction = auction
        self.royalty_params = royalty_params

    def serialize(self) -> Cell:
        """
        Serialize item state to Cell.

        Layout: owner:address content:^Cell auction:^Cell royalty_params:^Cell

        :return: Serialized state cell
        """
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_ref(self.content.serialize())
        cell.store_maybe_ref(self.auction.serialize() if self.auction else None)
        cell.store_ref(self.royalty_params.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemState:
        """
        Deserialize item state from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemState instance
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
    """Complete on-chain data for a Telegram item NFT contract."""

    def __init__(
        self,
        config: TeleItemConfig,
        state: t.Optional[TeleItemState] = None,
    ) -> None:
        """
        Initialize item data.

        :param config: Static item configuration
        :param state: Mutable item state (None if uninitialized)
        """
        self.config = config
        self.state = state

    def serialize(self) -> Cell:
        """
        Serialize item data to Cell.

        Layout: config:^Cell state:^Cell

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_ref(self.config.serialize())
        cell.store_maybe_ref(self.state.serialize() if self.state else None)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemData:
        """
        Deserialize item data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemData instance
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
    """On-chain data for a Telegram collection NFT contract."""

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
        Initialize collection data.

        :param touched: Whether collection has been initialized
        :param subwallet_id: Subwallet identifier for owner
        :param owner_key: Owner's public key
        :param content: Collection metadata (off-chain)
        :param item_code: Code cell for item contracts
        :param full_domain: Full domain name (e.g., "t.me")
        :param royalty_params: Royalty configuration for all items
        """
        self.touched = touched
        self.subwallet_id = subwallet_id
        self.owner_key = owner_key
        self.content = content
        self.item_code = item_code
        self.full_domain = full_domain
        self.royalty_params = royalty_params

    def serialize(self) -> Cell:
        """
        Serialize collection data to Cell.

        Layout: touched:bool subwallet_id:uint32 owner_key:uint256
                content:^Cell item_code:^Cell full_domain:^Cell royalty_params:^Cell

        :return: Serialized data cell
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
        """
        Deserialize collection data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleCollectionData instance
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
        Initialize start auction message body.

        :param auction_config: Auction configuration parameters
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.auction_config = auction_config

    def serialize(self) -> Cell:
        """
        Serialize start auction body to Cell.

        Layout: op_code:uint32 query_id:uint64 auction_config:^Cell

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.TELEITEM_START_AUCTION, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.auction_config.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemStartAuctionBody:
        """
        Deserialize start auction body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemStartAuctionBody instance
        """
        raise NotImplementedError


class TeleItemCancelAuctionBody(TlbScheme):
    """Message body for canceling an auction on a Telegram item."""

    def __init__(self, query_id: int = 0) -> None:
        """
        Initialize cancel auction message body.

        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize cancel auction body to Cell.

        Layout: op_code:uint32 query_id:uint64

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.TELEITEM_CANCEL_AUCTION, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TeleItemStartAuctionBody:
        """
        Deserialize cancel auction body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TeleItemCancelAuctionBody instance
        """
        raise NotImplementedError
