from __future__ import annotations

import abc
import typing as t

from pytoniq_core import Address, Cell, Transaction, begin_cell

from tonutils.types import (
    AddressLike,
    ContractStateInfo,
    ClientType,
    DNSCategory,
    NetworkGlobalID,
    WorkchainID,
)
from tonutils.utils import encode_dns_name

if t.TYPE_CHECKING:
    from tonutils.contracts.dns.tlb import (
        DNSRecordDNSNextResolver,
        DNSRecordWallet,
        DNSRecordStorage,
        DNSRecordSite,
        DNSRecords,
    )


class BaseClient(abc.ABC):
    TYPE: ClientType
    network: NetworkGlobalID

    @property
    @abc.abstractmethod
    def provider(self) -> t.Any:
        raise NotImplementedError

    @abc.abstractmethod
    async def __aenter__(self) -> BaseClient:
        raise NotImplementedError

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def _send_boc(self, boc: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_contract_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]:
        raise NotImplementedError

    @abc.abstractmethod
    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    async def send_boc(self, boc: str) -> None:
        await self._send_boc(boc)

    async def get_blockchain_config(self) -> t.Dict[int, t.Any]:
        return await self._get_blockchain_config()

    async def get_contract_info(self, address: AddressLike) -> ContractStateInfo:
        if isinstance(address, Address):
            address = Address(address).to_str(is_user_friendly=False)
        return await self._get_contract_info(address=address)

    async def get_contract_transactions(
        self,
        address: AddressLike,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]:
        if isinstance(address, Address):
            address = Address(address).to_str(is_user_friendly=False)
        return await self._get_contract_transactions(
            address=address,
            limit=limit,
            from_lt=from_lt,
            to_lt=to_lt,
        )

    async def run_get_method(
        self,
        address: AddressLike,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        if isinstance(address, Address):
            address = Address(address).to_str(is_user_friendly=False)
        return await self._run_get_method(
            address=address,
            method_name=method_name,
            stack=stack,
        )

    async def dnsresolve(
        self,
        domain: t.Union[str, bytes],
        category: DNSCategory,
        dns_root_address: t.Optional[AddressLike] = None,
    ) -> t.Optional[
        t.Union[
            Cell,
            DNSRecordDNSNextResolver,
            DNSRecordSite,
            DNSRecordStorage,
            DNSRecordWallet,
        ]
    ]:
        from tonutils.contracts.dns.tlb import DNSRecordDNSNextResolver, DNSRecords

        if isinstance(domain, str):
            domain = encode_dns_name(domain)
        if dns_root_address is None:
            blockchain_config = await self.get_blockchain_config()
            hash_part = blockchain_config[4].dns_root_addr
            dns_root_address = Address((WorkchainID.MASTERCHAIN.value, hash_part))

        domain_cell = begin_cell().store_snake_bytes(domain)

        res = await self.run_get_method(
            address=dns_root_address,
            method_name="dnsresolve",
            stack=[domain_cell.to_slice(), category.value],
        )
        if len(res) < 2:
            raise ValueError(f"`dnsresolve` returned {len(res)} items, but 2 expected.")

        blen = len(domain) * 8
        rlen = t.cast(int, res[0])
        cell = t.cast(Cell, res[1])

        if rlen % 8 != 0 or rlen > blen:
            raise ValueError(f"Invalid resolved length: result {rlen}, bytes {blen}.")
        if rlen == blen:
            # noinspection PyProtectedMember
            tcls = DNSRecords._DNS_RECORDS_CLASSES.get(category.name.lower())
            return tcls.deserialize(cell.begin_parse()) if tcls is not None else cell

        next_domain = domain[rlen // 8 :]
        next_dns_root = DNSRecordDNSNextResolver.deserialize(cell.begin_parse())
        return await self.dnsresolve(next_domain, category, next_dns_root.value)
