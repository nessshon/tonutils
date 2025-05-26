from typing import Optional, Union, Tuple

from pytoniq_core import Cell, begin_cell, Address

from .categories import *
from .op_codes import *
from .utils import (
    ByteHexConverter,
    DnsRecordParser,
    domain_to_bytes,
)
from ..cache import async_cache
from ..client import Client, TonapiClient
from ..utils import string_hash


class DNS:
    ROOT_DNS_ADDRESS = "Ef_lZ1T4NCb2mwkme9h2rJfESCE0W34ma9lWp7-_uY3zXDvq"  # noqa
    TESTNET_ROOT_DNS_ADDRESS = "Ef_v5x0Thgr6pq6ur2NvkWhIf4DxAxsL-Nk5rknT6n99oPKX"  # noqa

    @classmethod
    @async_cache(ttl=30)
    async def dnsresolve(
            cls,
            client: Client,
            address: Union[Address, str],
            domain: Cell,
            category: int,
    ) -> Tuple[int, Cell]:
        if isinstance(address, str):
            address = Address(address)

        # For Tonapi client, use `category` as hex string instead of int
        if isinstance(client, TonapiClient):
            category = hex(category)  # type: ignore

        method_result = await client.run_get_method(
            address=address.to_str(),
            method_name="dnsresolve",
            stack=[domain, category],
        )
        return method_result

    @classmethod
    async def _resolve(
            cls,
            client: Client,
            domain: bytes,
            category: str,
            dns_address: Union[Address, str],
    ) -> Union[Address, Cell, bytes, None]:
        result = await cls.dnsresolve(
            client,
            address=dns_address,
            domain=begin_cell().store_snake_bytes(domain).end_cell(),
            category=string_hash(category),
        )
        if len(result) != 2:
            raise ValueError("Invalid dnsresolve response")

        result_len, cell = result
        bit_len = len(domain) * 8

        if result_len == 0 or not cell:
            return None
        if isinstance(cell, list) and not cell:
            cell = None
        if result_len % 8 != 0 or result_len > bit_len:
            raise ValueError(f"Invalid result length {result_len}/{bit_len}")

        if result_len == bit_len:
            if category == DNS_NEXT_RESOLVER_CATEGORY:
                return DnsRecordParser.parse_next_resolver(cell)
            elif category == DNS_WALLET_CATEGORY:
                return DnsRecordParser.parse_wallet(cell)
            elif category == DNS_STORAGE_CATEGORY:
                return DnsRecordParser.parse_storage(cell)
            elif category == DNS_SITE_CATEGORY:
                return DnsRecordParser.parse_site(cell)
            return cell

        next_address = DnsRecordParser.parse_next_resolver(cell)
        remaining_domain = domain[result_len // 8:]
        return await cls._resolve(client, remaining_domain, category, next_address)

    @classmethod
    @async_cache(ttl=30)
    async def resolve(
            cls,
            client: Client,
            domain: str,
            category: str,
            dns_address: Optional[Union[Address, str]] = None,
    ) -> Union[Address, Cell, bytes, None]:
        if dns_address is None:
            try:
                blockchain_config = await client.get_config_params()
                dns_address = Address((-1, blockchain_config[4].dns_root_addr))
            except (Exception,):
                dns_address = (
                    cls.TESTNET_ROOT_DNS_ADDRESS
                    if client.is_testnet else
                    cls.ROOT_DNS_ADDRESS
                )
        if isinstance(dns_address, str):
            dns_address = Address(dns_address)

        domain_bytes = domain_to_bytes(domain)
        return await cls._resolve(client, domain_bytes, category, dns_address)

    @classmethod
    def _create_change_dns_cell(
            cls,
            name: str,
            record_value: Optional[Cell] = None,
            query_id: int = 0
    ) -> Cell:
        """
        Creates a Cell object to represent a change in a DNS record.

        :param name: The name of the DNS record to change.
        :param record_value: Optional Cell object containing the new value for the DNS record. If not provided, the record will be deleted.
        :param query_id: The query ID. Defaults to 0.
        :return: A Cell object representing the DNS record change.
        """
        cell = (
            begin_cell()
            .store_uint(CHANGE_DNS_RECORD_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_uint(string_hash(name), 256)
        )

        if record_value:
            cell.store_ref(record_value)

        return cell.end_cell()

    @staticmethod
    def _build_address_record_cell(opcode: int, address: Address) -> Cell:
        """
        Builds a Cell object containing an address and a specific opcode.

        :param opcode: The operation code (opcode) associated with the address.
        :param address: The Address object to include in the Cell.
        :return: A Cell object containing the opcode and the address.
        """
        return (
            begin_cell()
            .store_uint(opcode, 16)
            .store_address(address)
            .store_uint(0, 8)
            .end_cell()
        )

    @staticmethod
    def _build_site_record_cell(addr: Union[bytes, bytearray, str], is_storage: bool) -> Cell:
        """
        Builds a Cell object for setting a site or storage record.

        :param addr: The address (as bytes, bytearray, or string) of the site or storage.
        :param is_storage: Boolean indicating whether the record is for storage (True) or a regular site (False).
        :return: A Cell object representing the site or storage record.
        """
        opcode = PREFIX_STORAGE_CATEGORY if is_storage else PREFIX_SITE_CATEGORY
        return (
            begin_cell()
            .store_uint(opcode, 16)
            .store_bytes(ByteHexConverter(addr).bytes)
            .store_uint(0, 8)
            .end_cell()
        )

    @classmethod
    def build_set_next_resolver_record_body(cls, address: Address) -> Cell:
        """
        Builds a Cell object to set the next resolver record.

        :param address: The Address object representing the new next resolver.
        :return: A Cell object containing the next resolver record.
        """
        record_cell = cls._build_address_record_cell(PREFIX_NEXT_RESOLVER_CATEGORY, address)
        return cls._create_change_dns_cell(DNS_NEXT_RESOLVER_CATEGORY, record_cell)

    @classmethod
    def build_delete_next_resolver_record_body(cls) -> Cell:
        """
        Builds a Cell object to delete the next resolver record.

        :return: A Cell object to delete the next resolver record.
        """
        return cls._create_change_dns_cell(DNS_NEXT_RESOLVER_CATEGORY)

    @classmethod
    def build_set_wallet_record_body(cls, address: Address) -> Cell:
        """
        Builds a Cell object to set the wallet record.

        :param address: The Address object representing the new wallet.
        :return: A Cell object containing the wallet record.
        """
        record_cell = cls._build_address_record_cell(PREFIX_WALLET_CATEGORY, address)
        return cls._create_change_dns_cell(DNS_WALLET_CATEGORY, record_cell)

    @classmethod
    def build_delete_wallet_record_body(cls) -> Cell:
        """
        Builds a Cell object to delete the wallet record.

        :return: A Cell object to delete the wallet record.
        """
        return cls._create_change_dns_cell(DNS_WALLET_CATEGORY)

    @classmethod
    def build_set_site_record_body(
            cls,
            addr: Union[bytes, bytearray, str],
            is_storage: bool = False
    ) -> Cell:
        """
        Builds a Cell object to set a site record.

        :param addr: The address of the site as bytes, bytearray, or string.
        :param is_storage: Boolean indicating whether the site is for storage (True) or a regular site (False).
        :return: A Cell object containing the site record.
        """
        record_cell = cls._build_site_record_cell(addr, is_storage)
        return cls._create_change_dns_cell(DNS_SITE_CATEGORY, record_cell)

    @classmethod
    def build_delete_site_record_body(cls) -> Cell:
        """
        Builds a Cell object to delete the site record.

        :return: A Cell object to delete the site record.
        """
        return cls._create_change_dns_cell(DNS_SITE_CATEGORY)

    @classmethod
    def build_set_storage_record_body(cls, bag_id: Union[bytes, bytearray, str]) -> Cell:
        """
        Builds a Cell object to set the storage record.

        :param bag_id: The storage bag ID as bytes, bytearray, or string.
        :return: A Cell object containing the storage record.
        """
        record_cell = cls._build_site_record_cell(bag_id, is_storage=True)
        return cls._create_change_dns_cell(DNS_STORAGE_CATEGORY, record_cell)

    @classmethod
    def build_delete_storage_record_body(cls) -> Cell:
        """
        Builds a Cell object to delete the storage record.

        :return: A Cell object to delete the storage record.
        """
        return cls._create_change_dns_cell(DNS_STORAGE_CATEGORY)
