from typing import Optional, Union

from pytoniq_core import Cell, begin_cell, Address

from .categories import *
from .op_codes import *
from .utils import ByteHexConverter, hash_name


class Domain:

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
            .store_uint(hash_name(name), 256)
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
        opcode = SET_STORAGE_CATEGORY if is_storage else SET_SITE_CATEGORY
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
        record_cell = cls._build_address_record_cell(SET_NEXT_RESOLVER_CATEGORY, address)
        return cls._create_change_dns_cell("dns_next_resolver", record_cell)

    @classmethod
    def build_delete_next_resolver_record_body(cls) -> Cell:
        """
        Builds a Cell object to delete the next resolver record.

        :return: A Cell object to delete the next resolver record.
        """
        return cls._create_change_dns_cell("dns_next_resolver")

    @classmethod
    def build_set_wallet_record_body(cls, address: Address) -> Cell:
        """
        Builds a Cell object to set the wallet record.

        :param address: The Address object representing the new wallet.
        :return: A Cell object containing the wallet record.
        """
        record_cell = cls._build_address_record_cell(SET_WALLET_CATEGORY, address)
        return cls._create_change_dns_cell("wallet", record_cell)

    @classmethod
    def build_delete_wallet_record_body(cls) -> Cell:
        """
        Builds a Cell object to delete the wallet record.

        :return: A Cell object to delete the wallet record.
        """
        return cls._create_change_dns_cell("wallet")

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
        return cls._create_change_dns_cell("site", record_cell)

    @classmethod
    def build_delete_site_record_body(cls) -> Cell:
        """
        Builds a Cell object to delete the site record.

        :return: A Cell object to delete the site record.
        """
        return cls._create_change_dns_cell("site")

    @classmethod
    def build_set_storage_record_body(cls, bag_id: Union[bytes, bytearray, str]) -> Cell:
        """
        Builds a Cell object to set the storage record.

        :param bag_id: The storage bag ID as bytes, bytearray, or string.
        :return: A Cell object containing the storage record.
        """
        record_cell = cls._build_site_record_cell(bag_id, is_storage=True)
        return cls._create_change_dns_cell("storage", record_cell)

    @classmethod
    def build_delete_storage_record_body(cls) -> Cell:
        """
        Builds a Cell object to delete the storage record.

        :return: A Cell object to delete the storage record.
        """
        return cls._create_change_dns_cell("storage")
