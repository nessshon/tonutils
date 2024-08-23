from typing import Union, Optional

from pytoniq_core import Address, Cell, begin_cell

from .data import SubdomainManagerData
from .op_codes import UPDATE_RECORD_OPCODE
from ..categories import *
from ..utils import ByteHexConverter, hash_name
from ...contract import Contract


class SubdomainManager(Contract):
    CODE_HEX = "b5ee9c7241020a0100011d000114ff00f4a413f4bcf2c80b0102016202030202ce040500d3a1c61843ae92415270058001e5c08c45ae160f80012a04f1ae4205bc05e007ae93e00203f205f085060fe81edf42604384011c4705e033e04883dcb11fb64ddc4964ad1ba06b879240dc23572f37cc5caaab143a2ffe67bca06742438001246203c005060fe81edf42610201200607020120080900bb0ccc741d35c87e900c3c007e1071c17cb87d4831c0244c3834c7c0608414de8d246ea38db50074083e40be10a0c1fd03dbe84c00b4fff4c000700066350c1004e0c1fd05e5cc1620c1fd16cc38807e40be10a0c1fd05fe18bc00a44c38a0001b3b51343e90007e187d010c3e18a000193e10b23e1073c5bd00327b5520001d0824f4c1c0643a0835d244b5c8c060c6ad6ce1"  # noqa

    def __init__(
            self,
            admin_address: Union[Address, str],
            domains: Optional[Cell] = None,
            seed: Optional[int] = None,
    ) -> None:
        if isinstance(admin_address, str):
            admin_address = Address(admin_address)

        self._data = self.create_data(admin_address, domains, seed).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            admin_address: Union[Address, str],
            domains: Optional[Cell] = None,
            seed: Optional[int] = None,
    ) -> SubdomainManagerData:
        return SubdomainManagerData(admin_address, domains, seed)

    @classmethod
    def _create_update_dns_cell(cls, name: str, domain: str, record_value: Optional[Cell] = None) -> Cell:
        """
        Creates a Cell object to update a DNS record in the specified domain.

        :param name: The name of the DNS record to update.
        :param domain: The subdomain where the DNS record is located.
        :param record_value: Optional Cell object containing the value to set for the DNS record. If not provided, the record will be deleted.
        :return: A Cell object that represents the updated DNS record.
        """
        cell = (
            begin_cell()
            .store_uint(UPDATE_RECORD_OPCODE, 32)
            .store_ref(
                begin_cell()
                .store_snake_string(domain)
                .store_uint(0, 8)
                .end_cell()
            )
            .store_uint(hash_name(name), 256)
        )

        if record_value:
            cell.store_maybe_ref(record_value)

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
    def build_set_next_resolver_record_body(cls, domain: str, address: Address) -> Cell:
        """
        Builds a Cell object to set the next resolver record for the specified domain.

        :param domain: The subdomain for which the next resolver record is being set.
        :param address: The Address object representing the new resolver.
        :return: A Cell object containing the next resolver record for the domain.
        """
        record_cell = cls._build_address_record_cell(SET_NEXT_RESOLVER_CATEGORY, address)
        return cls._create_update_dns_cell("dns_next_resolver", domain, record_cell)

    @classmethod
    def build_delete_next_resolver_record_body(cls, domain: str) -> Cell:
        """
        Builds a Cell object to delete the next resolver record for the specified domain.

        :param domain: The subdomain for which the next resolver record is being deleted.
        :return: A Cell object to delete the next resolver record.
        """
        return cls._create_update_dns_cell("dns_next_resolver", domain)

    @classmethod
    def build_set_wallet_record_body(cls, domain: str, address: Address) -> Cell:
        """
        Builds a Cell object to set the wallet record for the specified domain.

        :param domain: The subdomain for which the wallet record is being set.
        :param address: The Address object representing the new wallet.
        :return: A Cell object containing the wallet record for the domain.
        """
        record_cell = cls._build_address_record_cell(SET_WALLET_CATEGORY, address)
        return cls._create_update_dns_cell("wallet", domain, record_cell)

    @classmethod
    def build_delete_wallet_record_body(cls, domain: str) -> Cell:
        """
        Builds a Cell object to delete the wallet record for the specified domain.

        :param domain: The subdomain for which the wallet record is being deleted.
        :return: A Cell object to delete the wallet record.
        """
        return cls._create_update_dns_cell("wallet", domain)

    @classmethod
    def build_set_site_record_body(
            cls,
            domain: str,
            addr: Union[bytes, bytearray, str],
            is_storage: bool = False,
    ) -> Cell:
        """
        Builds a Cell object to set a site record for the specified domain.

        :param domain: The subdomain for which the site record is being set.
        :param addr: The address of the site as bytes, bytearray, or string.
        :param is_storage: Boolean indicating whether the site is for storage (True) or a regular site (False).
        :return: A Cell object containing the site record for the domain.
        """
        record_cell = cls._build_site_record_cell(addr, is_storage)
        return cls._create_update_dns_cell("site", domain, record_cell)

    @classmethod
    def build_delete_site_record_body(cls, domain: str) -> Cell:
        """
        Builds a Cell object to delete the site record for the specified domain.

        :param domain: The subdomain for which the site record is being deleted.
        :return: A Cell object to delete the site record.
        """
        return cls._create_update_dns_cell("site", domain)

    @classmethod
    def build_set_storage_record_body(cls, domain: str, bag_id: Union[bytes, bytearray, str]) -> Cell:
        """
        Builds a Cell object to set the storage record for the specified domain.

        :param domain: The subdomain for which the storage record is being set.
        :param bag_id: The storage bag ID as bytes, bytearray, or string.
        :return: A Cell object containing the storage record for the domain.
        """
        record_cell = cls._build_site_record_cell(bag_id, is_storage=True)
        return cls._create_update_dns_cell("storage", domain, record_cell)

    @classmethod
    def build_delete_storage_record_body(cls, domain: str) -> Cell:
        """
        Builds a Cell object to delete the storage record for the specified domain.

        :param domain: The subdomain for which the storage record is being deleted.
        :return: A Cell object to delete the storage record.
        """
        return cls._create_update_dns_cell("storage", domain)
