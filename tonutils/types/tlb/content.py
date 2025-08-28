from __future__ import annotations

import hashlib
import typing as t

from pytoniq_core import (
    Builder,
    Cell,
    Slice,
    HashMap,
    begin_cell,
    TlbScheme,
)

from ...types.common import MetadataPrefix


class OnchainContent(TlbScheme):
    KNOWN_KEYS: t.List[str] = [
        "uri",
        "name",
        "image",
        "image_data",
        "cover_image",
        "cover_image_data",
        "amount_style",
        "description",
        "decimals",
        "symbol",
    ]

    def __init__(self, **kwargs: t.Any) -> None:
        self.data: t.Dict[str, str] = {
            key: (val if isinstance(val, str) else str(val))
            for key, val in kwargs.items()
        }

    @staticmethod
    def _hash_key(k: str) -> int:
        return int.from_bytes(hashlib.sha256(k.encode()).digest(), "big")

    @staticmethod
    def _value_serializer(v: str, b: Builder) -> Builder:
        cell = begin_cell()
        cell.store_uint(MetadataPrefix.ONCHAIN, 8)
        cell.store_snake_string(v)
        return b.store_ref(cell.end_cell())

    @staticmethod
    def _value_deserializer(s: Slice) -> str:
        s = s.load_ref().begin_parse()
        s.skip_bits(8)
        return s.load_snake_string()

    @classmethod
    def _parse_hashmap(
        cls,
        cs: Slice,
        known_keys: t.Optional[t.List[str]] = None,
    ) -> t.Dict[str, str]:
        known_keys = known_keys or []
        known_keys.extend(cls.KNOWN_KEYS)

        hashmap = cs.load_dict(
            key_length=256,
            value_deserializer=cls._value_deserializer,
        )

        out: t.Dict[str, str] = {}
        for key_name in known_keys:
            key_hash = cls._hash_key(key_name)
            if key_hash in hashmap:
                out[key_name] = hashmap[key_hash]

        return out

    def _build_hashmap(self) -> HashMap:
        hashmap = HashMap(
            256,
            value_serializer=self._value_serializer,
        )
        for key, val in self.data.items():
            hashmap.set(key, val, hash_key=True)
        return hashmap

    @classmethod
    def deserialize(
        cls,
        cs: Slice,
        with_prefix: bool,
        known_keys: t.Optional[t.List[str]] = None,
    ) -> OnchainContent:
        if with_prefix:
            cs.skip_bits(8)
        data = cls._parse_hashmap(cs, known_keys)
        return cls(**data)

    def serialize(self, with_prefix: bool) -> Cell:
        cell = begin_cell()
        if with_prefix:
            cell.store_uint(MetadataPrefix.ONCHAIN, 8)
        hashmap = self._build_hashmap()
        cell.store_dict(hashmap.serialize())
        return cell.end_cell()


class OffchainContent(TlbScheme):

    def __init__(self, uri: str) -> None:
        self.uri: str = uri

    @classmethod
    def deserialize(cls, cs: Slice, with_prefix: bool) -> OffchainContent:
        if with_prefix:
            cs.skip_bits(8)
        uri = cs.load_snake_string()
        return cls(uri=uri)

    def serialize(self, with_prefix: bool) -> Cell:
        cell = begin_cell()
        if with_prefix:
            cell.store_uint(MetadataPrefix.OFFCHAIN, 8)
        cell.store_snake_string(self.uri)
        return cell.end_cell()


class OffchainCommonContent(TlbScheme):

    def __init__(self, suffix_uri: str) -> None:
        self.suffix_uri = suffix_uri

    @classmethod
    def deserialize(cls, cs: Slice) -> OffchainCommonContent:
        uri = cs.load_snake_string()
        return cls(suffix_uri=uri)

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_snake_string(self.suffix_uri)
        return cell.end_cell()


class OffchainItemContent(TlbScheme):

    def __init__(self, prefix_uri: str) -> None:
        self.prefix_uri = prefix_uri

    @classmethod
    def deserialize(cls, cs: Slice) -> OffchainItemContent:
        uri = cs.load_snake_string()
        return cls(prefix_uri=uri)

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_snake_string(self.prefix_uri)
        return cell.end_cell()
