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


class BaseDNSRecord(TlbScheme, abc.ABC, t.Generic[TValue]):
    PREFIX: t.ClassVar[DNSPrefix]

    def __init__(self, value: t.Any) -> None:
        self.value: TValue = value

    @abc.abstractmethod
    def _build_cell(self) -> Cell: ...

    @classmethod
    @abc.abstractmethod
    def _parse_cell(cls, cs: Slice) -> t.Any: ...

    def serialize(self) -> Cell:
        return self._build_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> t.Any:
        return cls._parse_cell(cs)


class BaseDNSRecordAddress(BaseDNSRecord[Address]):

    def __init__(self, value: AddressLike) -> None:
        if not isinstance(value, Address):
            value = Address(value)
        super().__init__(value)

    def _build_cell(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.PREFIX, 16)
        cell.store_address(self.value)
        cell.store_uint(0, 8)
        return cell.end_cell()

    @classmethod
    def _parse_cell(cls, cs: Slice) -> BaseDNSRecordAddress:
        cs.skip_bits(16)
        return cls(cs.load_address())


class BaseDNSRecordBinary(BaseDNSRecord[Binary]):
    BINARY_CLS: t.ClassVar[t.Type[Binary]]

    def __init__(self, value: t.Union[Binary, BinaryLike]) -> None:
        if not isinstance(value, Binary):
            value = self.__class__.BINARY_CLS(value)
        super().__init__(value)

    def _build_cell(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.PREFIX, 16)
        cell.store_bytes(self.value.as_bytes)
        cell.store_uint(0, 8)
        return cell.end_cell()

    @classmethod
    def _parse_cell(cls, cs: Slice) -> BaseDNSRecordBinary:
        cs.skip_bits(16)
        return cls(cs.load_bytes(32))


class DNSRecordDNSNextResolver(BaseDNSRecordAddress):
    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.DNS_NEXT_RESOLVER

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordDNSNextResolver:
        return super().deserialize(cs)


class DNSRecordWallet(BaseDNSRecordAddress):
    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.WALLET

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordWallet:
        return super().deserialize(cs)


class DNSRecordStorage(BaseDNSRecordBinary):
    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.STORAGE
    BINARY_CLS: t.ClassVar[t.Type[BagID]] = BagID

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordStorage:
        return super().deserialize(cs)


class DNSRecordSite(BaseDNSRecordBinary):
    PREFIX: t.ClassVar[DNSPrefix] = DNSPrefix.SITE
    BINARY_CLS: t.ClassVar[t.Type[ADNL]] = ADNL

    @classmethod
    def deserialize(cls, cs: Slice) -> DNSRecordSite:
        return super().deserialize(cs)


class DNSRecords(OnchainContent):
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
        if isinstance(val, Cell):
            cs = val.begin_parse().load_ref().begin_parse()
            return record_cls.deserialize(cs)
        return record_cls(val)

    def _build_hashmap(self) -> HashMap:
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
        hashmap = super()._parse_hashmap(hashmap)
        for key in cls._DNS_KEYS:
            int_key = string_hash(key)
            if int_key in hashmap:
                val = hashmap.pop(int_key)
                cs = val.begin_parse().load_ref().begin_parse()
                hashmap[key] = cls._DNS_RECORDS_CLASSES[key].deserialize(cs)
        return hashmap


class TONDNSAuction(TlbScheme):

    def __init__(
        self,
        max_bid_address: AddressLike,
        max_bid_amount: int,
        auction_end_time: int,
    ) -> None:
        self.max_bid_address = max_bid_address
        self.max_bid_amount = max_bid_amount
        self.auction_end_time = auction_end_time

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_address(self.max_bid_address)
        cell.store_coins(self.max_bid_amount)
        cell.store_uint(self.auction_end_time, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TONDNSAuction:
        return cls(
            max_bid_address=cs.load_address(),
            max_bid_amount=cs.load_coins(),
            auction_end_time=cs.load_uint(64),
        )


class TONDNSCollectionData(TlbScheme):

    def __init__(
        self,
        content: OffchainContent,
        nft_item_code: Cell,
    ) -> None:
        self.content = content
        self.nft_item_code = nft_item_code

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_ref(self.content.serialize(True))
        cell.store_ref(self.nft_item_code)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TONDNSCollectionData:
        return cls(
            content=OffchainContent.deserialize(cs.load_ref().begin_parse(), True),
            nft_item_code=cs.load_ref(),
        )


class TONDNSItemData(TlbScheme):

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
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content
        self.domain = domain
        self.auction = auction
        self.last_fill_up_time = last_fill_up_time

    def serialize(self) -> Cell:
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
        self.query_id = query_id
        self.category = category
        self.record = record

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.CHANGE_DNS_RECORD, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_uint(self.category.value, 256)
        if self.record is not None:
            cell.store_ref(self.record.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> ChangeDNSRecordBody:
        raise NotImplementedError()


class RenewDNSBody(TlbScheme):

    def __init__(self, query_id: int = 0) -> None:
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.CHANGE_DNS_RECORD, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_uint(0, 256)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> RenewDNSBody:
        raise NotImplementedError()


class DNSBalanceReleaseBody(TlbScheme):

    def __int__(self, query_id: int = 0) -> None:
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.DNS_BALANCE_RELEASE, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> RenewDNSBody:
        raise NotImplementedError()
