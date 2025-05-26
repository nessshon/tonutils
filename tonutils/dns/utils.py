from typing import Union

from pytoniq_core import Cell, Address

from .categories import *
from ..client import Client


def domain_to_bytes(domain: str) -> bytes:
    if not domain:
        raise ValueError("empty domain")
    if domain == ".":
        return b"\x00"
    domain = domain.lower()

    if any(ord(c) <= 32 or 127 <= ord(c) <= 159 for c in domain):
        raise ValueError("invalid character in domain")
    parts = domain.split(".")

    if any(not part for part in parts):
        raise ValueError("domain name cannot have an empty component")
    raw = "\0".join(reversed(parts)) + "\0"

    return (("\0" + raw) if len(raw) < 126 else raw).encode()


class ByteHexConverter:

    def __init__(self, data: Union[bytes, bytearray, str]) -> None:
        self.bytes = self._convert_to_bytes(data)

    @staticmethod
    def _convert_to_bytes(data):
        if isinstance(data, (bytes, bytearray)):
            if len(data) != 32:
                raise ValueError("Invalid bytes length")
            return data

        if isinstance(data, str):
            if len(data) != 64:
                raise ValueError("Invalid hex length")
            return bytes.fromhex(data)

        raise TypeError("Unsupported type")

    def to_hex(self):
        return self.bytes.hex().zfill(64)


class DnsRecordParser:

    @classmethod
    def _assert_prefix(cls, slice_, expected: int, label: str):
        prefix = slice_.load_uint(16)
        if prefix != expected:
            raise ValueError(f"Invalid {label} prefix: {prefix:#x}")

    @classmethod
    def _parse_bytes_record(cls, cell: Cell, prefix: int, label: str) -> bytes:
        slice_ = cell.begin_parse()
        cls._assert_prefix(slice_, prefix, label)
        return slice_.load_bytes(32)

    @classmethod
    def _parse_address_record(cls, cell: Cell, prefix: int, label: str) -> Address:
        slice_ = cell.begin_parse()
        cls._assert_prefix(slice_, prefix, label)
        return slice_.load_address()

    @classmethod
    def parse_wallet(cls, cell: Cell) -> Address:
        return cls._parse_address_record(cell, PREFIX_WALLET_CATEGORY, "wallet")

    @classmethod
    def parse_next_resolver(cls, cell: Cell) -> Address:
        return cls._parse_address_record(cell, PREFIX_NEXT_RESOLVER_CATEGORY, "next resolver")

    @classmethod
    def parse_storage(cls, cell: Cell) -> bytes:
        return cls._parse_bytes_record(cell, PREFIX_STORAGE_CATEGORY, "storage bag ID")

    @classmethod
    def parse_site(cls, cell: Cell) -> bytes:
        prefix = cell.begin_parse().load_uint(16)

        if prefix == PREFIX_SITE_CATEGORY:
            return cls._parse_bytes_record(cell, PREFIX_SITE_CATEGORY, "ADNL")
        elif prefix == PREFIX_STORAGE_CATEGORY:
            return cls.parse_storage(cell)
        else:
            raise ValueError(f"Unknown site record prefix: {prefix:#x}")


async def resolve_wallet_address(client: Client, value: Union[Address, str]) -> Address:
    """
    Convert input (Address, address string, or .ton/.t.me domain) into a valid Address.

    :param client: TON client instance.
    :param value: Address object, address string, or a .ton/.t.me domain.
    :return: Resolved Address object.
    """
    from . import DNS
    if isinstance(value, Address):
        return value

    if not isinstance(value, str):
        raise ValueError("Input must be a string or Address instance")

    if value.endswith((".ton", ".t.me")):
        address = await DNS.resolve(client, value, DNS_WALLET_CATEGORY)
        if not isinstance(address, Address):
            raise TypeError("Unable to resolve wallet address from domain")
        return address

    return Address(value)
