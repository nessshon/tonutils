from __future__ import annotations

import abc
import typing as t

from pytoniq_core import Address, Cell, HashMap, Slice, TlbScheme, begin_cell

from tonutils.contracts.nft.tlb import OnchainContent, OffchainContent
from tonutils.contracts.opcodes import OpCode
from tonutils.types import (
    AddressLike,
    ADNL,
    BagID,
    Binary,
    BinaryLike,
    DNSCategory,
    DNSPrefix,
)
from tonutils.utils import string_hash

TValue = t.TypeVar("TValue")

ALLOWED_DNS_ZONES = (".ton", ".t.me")
"""Allowed DNS zone suffixes for TON domains."""


class BaseDNSRecord(TlbScheme, abc.ABC, t.Generic[TValue]):
    """Abstract base class for DNS record types."""

    PREFIX: t.ClassVar[DNSPrefix]
    """DNS record type prefix identifier."""

    def __init__(self, value: t.Any) -> None:
        """
        Initialize DNS record with value.

        :param value: Record value (type depends on subclass)
        """
        self.value: TValue = value

    @abc.abstractmethod
    def _build_cell(self) -> Cell:
        """
        Build Cell from record value.

        :return: Serialized record cell
        """

    @classmethod
    @abc.abstractmethod
    def _parse_cell(cls, cs: Slice) -> t.Any:
        """
        Parse record value from Cell slice.

        :param cs: Cell slice to parse from
        :return: Parsed record instance
        """

    def serialize(self) -> Cell:
        """
        Serialize DNS record to Cell.

        :return: Serialized record cell
        """
        return self._build_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> t.Any:
        """
        Deserialize DNS record from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized record instance
        """
        return cls._parse_cell(cs)


class BaseDNSRecordAddress(BaseDNSRecord[Address]):
    """Base class for DNS records containing TON addresses."""

    def __init__(self, value: AddressLike) -> None:
        """
        Initialize address DNS record.

        :param value: TON address (Address object or string)
        """
        if not isinstance(value, Address):
            value = Address(value)
        super().__init__(value)

    def _build_cell(self) -> Cell:
        """
        Build Cell from address value.

        Layout: prefix:uint16 address:address padding:uint8

        :return: Serialized record cell
        """
        cell = begin_cell()
        cell.store_uint(self.PREFIX, 16)
        cell.store_address(self.value)
        cell.store_uint(0, 8)
        return cell.end_cell()

    @classmethod
    def _parse_cell(cls, cs: Slice) -> BaseDNSRecordAddress:
        """
        Parse address record from Cell slice.

        :param cs: Cell slice to parse from
        :return: Parsed address record instance
        """
        cs.skip_bits(16)
        return cls(cs.load_address())


class BaseDNSRecordBinary(BaseDNSRecord[Binary]):
    """Base class for DNS records containing binary data."""

    BINARY_CLS: t.ClassVar[t.Type[Binary]]
    """Binary data class for this record type."""

    def __init__(self, value: t.Union[Binary, BinaryLike]) -> None:
        """
        Initialize binary DNS record.

        :param value: Binary data (Binary object or bytes/hex string)
        """
        if not isinstance(value, Binary):
            value = self.__class__.BINARY_CLS(value)
        super().__init__(value)

    def _build_cell(self) -> Cell:
        """
        Build Cell from binary value.

        Layout: prefix:uint16 data:bytes(32) padding:uint8

        :return: Serialized record cell
        """
        cell = begin_cell()
        cell.store_uint(self.PREFIX, 16)
        cell.store_bytes(self.value.as_bytes)
        cell.store_uint(0, 8)
        return cell.end_cell()

    @classmethod
    def _parse_cell(cls, cs: Slice) -> BaseDNSRecordBinary:
        """
        Parse binary record from Cell slice.

        :param cs: Cell slice to parse from
        :return: Parsed binary record instance
        """
        cs.skip_bits(16)
        return cls(cs.load_bytes(32))


class DNSRecordDNSNextResolver(BaseDNSRecordAddress):
    """DNS record pointing to next resolver contract."""

    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.DNS_NEXT_RESOLVER

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordDNSNextResolver:
        """
        Deserialize next resolver record from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized DNSRecordDNSNextResolver instance
        """
        return super().deserialize(cs)


class DNSRecordWallet(BaseDNSRecordAddress):
    """DNS record pointing to wallet address."""

    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.WALLET

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordWallet:
        """
        Deserialize wallet record from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized DNSRecordWallet instance
        """
        return super().deserialize(cs)


class DNSRecordStorage(BaseDNSRecordBinary):
    """DNS record pointing to TON Storage bag."""

    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.STORAGE
    BINARY_CLS: t.ClassVar[t.Type[BagID]] = BagID

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordStorage:
        """
        Deserialize storage record from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized DNSRecordStorage instance
        """
        return super().deserialize(cs)


class DNSRecordSite(BaseDNSRecordBinary):
    """DNS record pointing to TON Site (ADNL address)."""

    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.SITE
    BINARY_CLS: t.ClassVar[t.Type[ADNL]] = ADNL

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordSite:
        """
        Deserialize site record from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized DNSRecordSite instance
        """
        return super().deserialize(cs)


class DNSRecords(OnchainContent):
    """Collection of DNS records for a domain."""

    _DNS_RECORDS_CLASSES: t.Dict[str, t.Type[BaseDNSRecord]] = {
        "dns_next_resolver": DNSRecordDNSNextResolver,
        "storage": DNSRecordStorage,
        "wallet": DNSRecordWallet,
        "site": DNSRecordSite,
    }
    """Mapping of record names to record classes."""

    _DNS_CATEGORIES: t.Dict[int, str] = {
        DNSCategory.DNS_NEXT_RESOLVER: "dns_next_resolver",
        DNSCategory.STORAGE: "storage",
        DNSCategory.WALLET: "wallet",
        DNSCategory.SITE: "site",
    }
    """Mapping of category integers to record names."""

    _DNS_KEYS: t.Set[str] = set(_DNS_RECORDS_CLASSES.keys())
    """Set of recognized DNS record keys."""

    def __init__(self, data: t.Dict[t.Union[str, int], t.Any]) -> None:
        """
        Initialize DNS records collection.

        Separates DNS-specific records from other metadata.

        :param data: Dictionary of record keys to values
        """
        self.records: t.Dict[t.Union[str, int], BaseDNSRecord] = {}
        """DNS-specific records (wallet, site, storage, etc.)."""

        other: t.Dict[t.Union[str, int], t.Any] = {}

        for raw_key, val in data.items():
            if isinstance(raw_key, int) and raw_key in self._DNS_CATEGORIES:
                key: str = self._DNS_CATEGORIES[raw_key]
            elif isinstance(raw_key, str):
                key = raw_key
            else:
                other[raw_key] = val
                continue
            if key not in self._DNS_KEYS:
                other[raw_key] = val
                continue
            if not isinstance(val, BaseDNSRecord):
                record_cls = self._DNS_RECORDS_CLASSES[key]
                val = self._to_record(record_cls, val)
            self.records[key] = val

        super().__init__(other)

    @classmethod
    def _to_record(cls, record_cls: t.Type[BaseDNSRecord], val: t.Any) -> BaseDNSRecord:
        """
        Convert value to DNS record instance.

        :param record_cls: Record class to instantiate
        :param val: Value to convert (Cell or raw value)
        :return: DNS record instance
        """
        if isinstance(val, Cell):
            cs = val.begin_parse().load_ref().begin_parse()
            return record_cls.deserialize(cs)
        return record_cls(val)

    def _build_hashmap(self) -> HashMap:
        """
        Build hashmap from records and metadata.

        :return: HashMap with all records and metadata
        """
        hashmap = super()._build_hashmap()
        for key, val in self.records.items():
            if isinstance(key, str):
                key = string_hash(key)
            hashmap.set_int_key(key, val.serialize())
        return hashmap

    @classmethod
    def _parse_hashmap(
        cls,
        hashmap: t.Dict[t.Union[str, int], Cell],
    ) -> t.Dict[t.Union[str, int], t.Any]:
        """
        Parse hashmap and deserialize DNS records.

        :param hashmap: Raw hashmap from deserialization
        :return: Parsed dictionary with deserialized records
        """
        hashmap = super()._parse_hashmap(hashmap)
        for key in cls._DNS_KEYS:
            int_key = string_hash(key)
            if int_key in hashmap:
                val = hashmap.pop(int_key)
                cs = val.begin_parse().load_ref().begin_parse()
                hashmap[key] = cls._DNS_RECORDS_CLASSES[key].deserialize(cs)
        return hashmap


class TONDNSAuction(TlbScheme):
    """Auction state for TON DNS domain."""

    def __init__(
        self,
        max_bid_address: AddressLike,
        max_bid_amount: int,
        auction_end_time: int,
    ) -> None:
        """
        Initialize DNS auction state.

        :param max_bid_address: Address of highest bidder
        :param max_bid_amount: Highest bid amount in nanotons
        :param auction_end_time: Unix timestamp when auction ends
        """
        self.max_bid_address = max_bid_address
        self.max_bid_amount = max_bid_amount
        self.auction_end_time = auction_end_time

    def serialize(self) -> Cell:
        """
        Serialize auction state to Cell.

        Layout: max_bid_address:address max_bid_amount:coins auction_end_time:uint64

        :return: Serialized auction cell
        """
        cell = begin_cell()
        cell.store_address(self.max_bid_address)
        cell.store_coins(self.max_bid_amount)
        cell.store_uint(self.auction_end_time, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TONDNSAuction:
        """
        Deserialize auction state from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TONDNSAuction instance
        """
        return cls(
            max_bid_address=cs.load_address(),
            max_bid_amount=cs.load_coins(),
            auction_end_time=cs.load_uint(64),
        )


class TONDNSCollectionData(TlbScheme):
    """On-chain data for TON DNS collection contract."""

    def __init__(
        self,
        content: OffchainContent,
        nft_item_code: Cell,
    ) -> None:
        """
        Initialize DNS collection data.

        :param content: Collection metadata (off-chain)
        :param nft_item_code: Code cell for DNS item contracts
        """
        self.content = content
        self.nft_item_code = nft_item_code

    def serialize(self) -> Cell:
        """
        Serialize collection data to Cell.

        Layout: content:^Cell nft_item_code:^Cell

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_ref(self.content.serialize(True))
        cell.store_ref(self.nft_item_code)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TONDNSCollectionData:
        """
        Deserialize collection data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TONDNSCollectionData instance
        """
        return cls(
            content=OffchainContent.deserialize(cs.load_ref().begin_parse(), True),
            nft_item_code=cs.load_ref(),
        )


class TONDNSItemData(TlbScheme):
    """On-chain data for TON DNS item (domain) contract."""

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OnchainContent,
        domain: str,
        last_fill_up_time: int,
        auction: t.Optional[TONDNSAuction] = None,
    ) -> None:
        """
        Initialize DNS item data.

        :param index: Item index within collection
        :param collection_address: Parent collection address
        :param owner_address: Current domain owner address
        :param content: On-chain DNS records and metadata
        :param domain: Domain name string
        :param last_fill_up_time: Unix timestamp of last renewal
        :param auction: Active auction state (None if no auction)
        """
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content
        self.domain = domain
        self.auction = auction
        self.last_fill_up_time = last_fill_up_time

    def serialize(self) -> Cell:
        """
        Serialize item data to Cell.

        Layout: index:uint256 collection:address owner:address content:^Cell
                domain:^Cell auction:dict last_fill_up_time:uint64

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_uint(self.index, 256)
        cell.store_address(self.collection_address)
        cell.store_address(self.owner_address)
        cell.store_ref(self.content.serialize(True))
        cell.store_ref(begin_cell().store_snake_string(self.domain).end_cell())
        cell.store_dict(self.auction.serialize() if self.auction else None)
        cell.store_uint(self.last_fill_up_time, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TONDNSItemData:
        """
        Deserialize item data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TONDNSItemData instance
        """
        return cls(
            index=cs.load_uint(256),
            collection_address=cs.load_address(),
            owner_address=cs.load_address(),
            content=OnchainContent.deserialize(cs.load_ref().begin_parse(), True),
            domain=cs.load_ref().begin_parse().load_snake_string(),
            auction=(
                TONDNSAuction.deserialize(cs.load_ref().begin_parse())
                if cs.remaining_refs > 0
                else None
            ),
            last_fill_up_time=cs.load_uint(64),
        )


class ChangeDNSRecordBody(TlbScheme):
    """Message body for changing DNS record."""

    def __init__(
        self,
        category: DNSCategory,
        record: t.Optional[
            t.Union[
                DNSRecordDNSNextResolver,
                DNSRecordSite,
                DNSRecordStorage,
                DNSRecordWallet,
            ]
        ] = None,
        query_id: int = 0,
    ) -> None:
        """
        Initialize change DNS record message body.

        :param category: DNS record category to change
        :param record: New record value (None to delete record)
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.category = category
        self.record = record

    def serialize(self) -> Cell:
        """
        Serialize change record body to Cell.

        Layout: op_code:uint32 query_id:uint64 category:uint256 [record:^Cell]

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.CHANGE_DNS_RECORD, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_uint(self.category.value, 256)
        if self.record is not None:
            cell.store_ref(self.record.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> ChangeDNSRecordBody:
        """
        Deserialize change record body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized ChangeDNSRecordBody instance
        """
        raise NotImplementedError


class RenewDNSBody(TlbScheme):
    """Message body for renewing DNS domain."""

    def __init__(self, query_id: int = 0) -> None:
        """
        Initialize renew DNS message body.

        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize renew body to Cell.

        Layout: op_code:uint32 query_id:uint64 zero:uint256

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.CHANGE_DNS_RECORD, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_uint(0, 256)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> RenewDNSBody:
        """
        Deserialize renew body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized RenewDNSBody instance
        """
        raise NotImplementedError


class DNSBalanceReleaseBody(TlbScheme):
    """Message body for releasing DNS domain balance."""

    def __int__(self, query_id: int = 0) -> None:
        """
        Initialize balance release message body.

        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize balance release body to Cell.

        Layout: op_code:uint32 query_id:uint64

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.DNS_BALANCE_RELEASE, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> RenewDNSBody:
        """
        Deserialize balance release body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized DNSBalanceReleaseBody instance
        """
        raise NotImplementedError
