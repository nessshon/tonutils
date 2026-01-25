from __future__ import annotations

import abc
import asyncio
import typing as t
from contextlib import suppress

from pytoniq_core import Address, Cell, Transaction, begin_cell

from tonutils.exceptions import ProviderError
from tonutils.types import (
    AddressLike,
    ContractInfo,
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
    """Abstract base class for TON blockchain clients."""

    TYPE: ClientType
    """Type of the underlying client implementation (HTTP or ADNL)."""

    network: NetworkGlobalID
    """Global network identifier the client is operating on (MAINNET or TESTNET)."""

    @property
    @abc.abstractmethod
    def connected(self) -> bool:
        """
        Check whether provider resources are initialized and usable.

        :return: True if client has an active session/connection, False otherwise
        """

    @property
    @abc.abstractmethod
    def provider(self) -> t.Any:
        """
        Underlying transport/provider backend used for all requests.

        Expected to expose network I/O primitives appropriate for the client
        type (HTTP session, ADNL transport, etc.).
        """

    @abc.abstractmethod
    async def connect(self) -> None:
        """Initialize any required provider resources (sessions, transports, etc.)."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Close provider resources. Should be safe to call multiple times."""

    @abc.abstractmethod
    async def _send_message(self, boc: str) -> None: ...

    @abc.abstractmethod
    async def _get_config(self) -> t.Dict[int, t.Any]: ...

    @abc.abstractmethod
    async def _get_info(self, address: str) -> ContractInfo: ...

    @abc.abstractmethod
    async def _get_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = None,
    ) -> t.List[Transaction]: ...

    @abc.abstractmethod
    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]: ...

    async def __aenter__(self) -> BaseClient:
        """
        Prepare client resources for use.

        Should initialize network connections or sessions as required.
        """
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        """
        Release allocated client resources.

        Called automatically when the async context ends.
        """
        with suppress(asyncio.CancelledError):
            await self.close()

    async def send_message(self, boc: str) -> None:
        """
        Send an external message to the blockchain.

        :param boc: Message body serialized as BoC string, in a format accepted by the underlying provider
        """
        await self._send_message(boc)

    async def get_config(self) -> t.Dict[int, t.Any]:
        """
        Fetch and decode global blockchain configuration.

        :return: Mapping of configuration parameter ID to parsed value
        """
        return await self._get_config()

    async def get_info(self, address: AddressLike) -> ContractInfo:
        """
        Fetch basic state information for a smart contract.

        :param address: Contract address as Address object or string
        :return: ContractInfo with code, data, balance and last tx data
        """
        if isinstance(address, Address):
            address = Address(address).to_str(is_user_friendly=False)
        return await self._get_info(address=address)

    async def get_transactions(
        self,
        address: AddressLike,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = None,
    ) -> t.List[Transaction]:
        """
        Fetch transaction history for a contract.

        :param address: Contract address as Address object or string
        :param limit: Maximum number of transactions to return
        :param from_lt: Upper bound logical time (inclusive).
            If None, starts from the most recent transaction.
        :param to_lt: Lower bound logical time (exclusive).
            If None or 0, no lower bound is applied.
        :return: List of Transaction objects ordered from newest to oldest
        """
        if isinstance(address, Address):
            address = Address(address).to_str(is_user_friendly=False)
        return await self._get_transactions(
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
        """
        Execute a smart-contract get-method.

        :param address: Contract address as Address object or string
        :param method_name: Name of the get-method to execute
        :param stack: Optional initial TVM stack items for the call
        :return: Decoded TVM stack items returned by the method
        """
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
        """
        Resolve a TON DNS record.

        :param domain: Domain name as UTF-8 string or encoded DNS bytes
        :param category: DNS record category to resolve
        :param dns_root_address: Optional custom DNS root contract address;
            if omitted, value is taken from config param 4
        :return: Parsed DNS record for the requested category, or raw Cell
            if record type is unknown; None if nothing is resolved
        """
        from tonutils.contracts.dns.tlb import DNSRecordDNSNextResolver, DNSRecords

        if isinstance(domain, str):
            domain = encode_dns_name(domain)
        if dns_root_address is None:
            blockchain_config = await self.get_config()
            hash_part = blockchain_config[4].dns_root_addr
            dns_root_address = Address((WorkchainID.MASTERCHAIN.value, hash_part))

        domain_cell = begin_cell().store_snake_bytes(domain)

        res = await self.run_get_method(
            address=dns_root_address,
            method_name="dnsresolve",
            stack=[domain_cell.to_slice(), category.value],
        )
        if len(res) < 2:
            raise ProviderError(
                f"dnsresolve failed: invalid response (expected 2 stack items, got {len(res)})"
            )

        blen = len(domain) * 8
        rlen = t.cast(int, res[0])

        cell = res[1]

        if cell is None:
            return None

        if rlen % 8 != 0 or rlen > blen:
            raise ProviderError(
                f"dnsresolve failed: invalid resolved length {rlen} bits (domain {blen} bits)"
            )
        if rlen == blen:
            # noinspection PyProtectedMember
            tcls = DNSRecords._DNS_RECORDS_CLASSES.get(category.name.lower())
            return tcls.deserialize(cell.begin_parse()) if tcls is not None else cell

        next_domain = domain[rlen // 8 :]
        next_dns_root = DNSRecordDNSNextResolver.deserialize(cell.begin_parse())
        return await self.dnsresolve(next_domain, category, next_dns_root.value)
