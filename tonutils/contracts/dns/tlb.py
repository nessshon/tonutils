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

_TValue = t.TypeVar("_TValue")


class BaseDNSRecord(TlbScheme, abc.ABC, t.Generic[_TValue]):
    """Abstract base for DNS record types."""

    PREFIX: t.ClassVar[DNSPrefix]

    def __init__(self, value: t.Any) -> None:
        """
        :param value: Record value (type depends on subclass).
        """
        self.value: _TValue = value

    @abc.abstractmethod
    def _build_cell(self) -> Cell:
        """Build `Cell` from record value."""

    @classmethod
    @abc.abstractmethod
    def _parse_cell(cls, cs: Slice) -> t.Any:
        """Parse record value from `Slice`.

        :param cs: Source slice.
        """

    def serialize(self) -> Cell:
        """Serialize to `Cell`."""
        return self._build_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> t.Any:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls._parse_cell(cs)


class BaseDNSRecordAddress(BaseDNSRecord[Address]):
    """Base for DNS records containing TON addresses."""

    def __init__(self, value: AddressLike) -> None:
        """
        :param value: TON address.
        """
        if not isinstance(value, Address):
            value = Address(value)
        super().__init__(value)

    def _build_cell(self) -> Cell:
        """Build `Cell` from address value.

        TLB: `prefix:uint16 address:address padding:uint8`
        """
        cell = begin_cell()
        cell.store_uint(self.PREFIX, 16)
        cell.store_address(self.value)
        cell.store_uint(0, 8)
        return cell.end_cell()

    @classmethod
    def _parse_cell(cls, cs: Slice) -> BaseDNSRecordAddress:
        """Parse address record from `Slice`.

        :param cs: Source slice.
        """
        cs.skip_bits(16)
        return cls(cs.load_address())


class BaseDNSRecordBinary(BaseDNSRecord[Binary]):
    """Base for DNS records containing binary data."""

    BINARY_CLS: t.ClassVar[t.Type[Binary]]

    def __init__(self, value: t.Union[Binary, BinaryLike]) -> None:
        """
        :param value: Binary data.
        """
        if not isinstance(value, Binary):
            value = self.__class__.BINARY_CLS(value)
        super().__init__(value)

    def _build_cell(self) -> Cell:
        """Build `Cell` from binary value.

        TLB: `prefix:uint16 data:bytes(32) padding:uint8`
        """
        cell = begin_cell()
        cell.store_uint(self.PREFIX, 16)
        cell.store_bytes(self.value.as_bytes)
        cell.store_uint(0, 8)
        return cell.end_cell()

    @classmethod
    def _parse_cell(cls, cs: Slice) -> BaseDNSRecordBinary:
        """Parse binary record from `Slice`.

        :param cs: Source slice.
        """
        cs.skip_bits(16)
        return cls(cs.load_bytes(32))


class DNSRecordDNSNextResolver(BaseDNSRecordAddress):
    """DNS record pointing to next resolver contract."""

    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.DNS_NEXT_RESOLVER

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordDNSNextResolver:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return super().deserialize(cs)


class DNSRecordWallet(BaseDNSRecordAddress):
    """DNS record pointing to wallet address."""

    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.WALLET

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordWallet:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return super().deserialize(cs)


class DNSRecordStorage(BaseDNSRecordBinary):
    """DNS record pointing to TON Storage bag."""

    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.STORAGE
    BINARY_CLS: t.ClassVar[t.Type[BagID]] = BagID

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordStorage:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return super().deserialize(cs)


class DNSRecordSite(BaseDNSRecordBinary):
    """DNS record pointing to TON Site (ADNL address)."""

    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.SITE
    BINARY_CLS: t.ClassVar[t.Type[ADNL]] = ADNL

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordSite:
        """Deserialize from `Slice`.

        :param cs: Source slice.
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

    _DNS_CATEGORIES: t.Dict[int, str] = {
        DNSCategory.DNS_NEXT_RESOLVER: "dns_next_resolver",
        DNSCategory.STORAGE: "storage",
        DNSCategory.WALLET: "wallet",
        DNSCategory.SITE: "site",
    }

    _DNS_KEYS: t.Set[str] = set(_DNS_RECORDS_CLASSES.keys())

    def __init__(self, data: t.Dict[t.Union[str, int], t.Any]) -> None:
        """
        :param data: Record keys to values.
        """
        self.records: t.Dict[t.Union[str, int], BaseDNSRecord] = {}

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
        """Convert a value to a `BaseDNSRecord` instance.

        :param record_cls: Target record class.
        :param val: Value to convert (`Cell` or raw value).
        :return: DNS record instance.
        """
        if isinstance(val, Cell):
            cs = val.begin_parse().load_ref().begin_parse()
            return record_cls.deserialize(cs)
        return record_cls(val)

    def _build_hashmap(self) -> HashMap:
        """Build `HashMap` from records and metadata.

        :return: Serializable `HashMap`.
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
        """Parse hashmap and deserialize DNS records.

        :param hashmap: Raw deserialized hashmap.
        :return: Parsed dictionary with deserialized records.
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
    """Auction state for a TON DNS domain."""

    def __init__(
        self,
        max_bid_address: AddressLike,
        max_bid_amount: int,
        auction_end_time: int,
    ) -> None:
        """
        :param max_bid_address: Highest bidder address.
        :param max_bid_amount: Highest bid in nanotons.
        :param auction_end_time: Auction end unix timestamp.
        """
        self.max_bid_address = max_bid_address
        self.max_bid_amount = max_bid_amount
        self.auction_end_time = auction_end_time

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `max_bid_address:address max_bid_amount:coins auction_end_time:uint64`
        """
        cell = begin_cell()
        cell.store_address(self.max_bid_address)
        cell.store_coins(self.max_bid_amount)
        cell.store_uint(self.auction_end_time, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TONDNSAuction:
        """Deserialize from `Slice`.

        :param cs: Source slice.
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
        :param content: Off-chain collection metadata.
        :param nft_item_code: Code cell for DNS item contracts.
        """
        self.content = content
        self.nft_item_code = nft_item_code

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `content:^Cell nft_item_code:^Cell`
        """
        cell = begin_cell()
        cell.store_ref(self.content.serialize(True))
        cell.store_ref(self.nft_item_code)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TONDNSCollectionData:
        """Deserialize from `Slice`.

        :param cs: Source slice.
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
        :param index: Item index within collection.
        :param collection_address: Parent collection address.
        :param owner_address: Current domain owner address.
        :param content: On-chain DNS records and metadata.
        :param domain: Domain name string.
        :param last_fill_up_time: Last renewal unix timestamp.
        :param auction: Active auction state, or `None`.
        """
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content
        self.domain = domain
        self.auction = auction
        self.last_fill_up_time = last_fill_up_time

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `index:uint256 collection:address owner:address content:^Cell
        domain:^Cell auction:dict last_fill_up_time:uint64`
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
        """Deserialize from `Slice`.

        :param cs: Source slice.
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
    """Message body for changing a DNS record."""

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
        :param category: DNS record category to change.
        :param record: New record value, or `None` to delete.
        :param query_id: Query identifier.
        """
        self.query_id = query_id
        self.category = category
        self.record = record

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 category:uint256 [record:^Cell]`
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
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class RenewDNSBody(TlbScheme):
    """Message body for renewing a DNS domain."""

    def __init__(self, query_id: int = 0) -> None:
        """
        :param query_id: Query identifier.
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 zero:uint256`
        """
        cell = begin_cell()
        cell.store_uint(OpCode.CHANGE_DNS_RECORD, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_uint(0, 256)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> RenewDNSBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class DNSBalanceReleaseBody(TlbScheme):
    """Message body for releasing DNS domain balance."""

    def __int__(self, query_id: int = 0) -> None:
        """
        :param query_id: Query identifier.
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64`
        """
        cell = begin_cell()
        cell.store_uint(OpCode.DNS_BALANCE_RELEASE, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> RenewDNSBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError
