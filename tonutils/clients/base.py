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
    """Abstract base class for TON blockchain clients."""

    TYPE: ClientType
    """Type of the underlying client implementation (HTTP or ADNL)."""

    network: NetworkGlobalID
    """Global network identifier the client is operating on (MAINNET or TESTNET)."""

    @property
    @abc.abstractmethod
    def provider(self) -> t.Any:
        """
        Underlying transport/provider backend used for all requests.

        Expected to expose network I/O primitives appropriate for the client
        type (HTTP session, ADNL transport, etc.).
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def __aenter__(self) -> BaseClient:
        """
        Prepare client resources for use.

        Should initialize network connections or sessions as required.
        """
        raise NotImplementedError

    @abc.abstractmethod
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
        raise NotImplementedError

    @abc.abstractmethod
    async def _send_boc(self, boc: str) -> None:
        """
        Send an external message to the network using the underlying provider.

        :param boc: Message body serialized as BoC string,
            in a format accepted by the underlying provider
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        """
        Fetch full blockchain configuration from the underlying provider.

        :return: Mapping of configuration parameter ID to parsed value
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        """
        Retrieve basic contract state information from the provider.

        :param address: Contract address in raw
        :return: ContractStateInfo with basic state, balance and last tx data
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_contract_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]:
        """
        Fetch a list of recent contract transactions from the provider.

        :param address: Contract address in raw
        :param limit: Maximum number of transactions to return
        :param from_lt: Optional lower bound (exclusive) logical time
        :param to_lt: Upper bound (inclusive) logical time, 0 means latest
        :return: List of Transaction objects ordered from newest to oldest
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        """
        Execute a contract get-method via the provider.

        :param address: Contract address in raw
        :param method_name: Name of the get-method to execute
        :param stack: Optional initial TVM stack items for the call
        :return: Decoded TVM stack items returned by the method
        """
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        """
        Check whether provider resources are initialized and usable.

        :return: True if client has an active session/connection, False otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def connect(self) -> None:
        """Initialize any required provider resources (sessions, transports, etc.)."""
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        """Close provider resources. Should be safe to call multiple times."""
        raise NotImplementedError

    async def send_boc(self, boc: str) -> None:
        """
        Send an external message to the blockchain.

        :param boc: Message body serialized as BoC string, in a format accepted by the underlying provider
        """
        await self._send_boc(boc)

    async def get_blockchain_config(self) -> t.Dict[int, t.Any]:
        """
        Fetch and decode global blockchain configuration.

        :return: Mapping of configuration parameter ID to parsed value
        """
        return await self._get_blockchain_config()

    async def get_contract_info(self, address: AddressLike) -> ContractStateInfo:
        """
        Fetch basic state information for a smart contract.

        :param address: Contract address as Address object or string
        :return: ContractStateInfo with code, data, balance and last tx data
        """
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
        """
        Fetch transaction history for a contract.

        :param address: Contract address as Address object or string
        :param limit: Maximum number of transactions to return
        :param from_lt: Optional lower bound (exclusive) logical time
        :param to_lt: Upper bound (inclusive) logical time, 0 means latest
        :return: List of Transaction objects ordered from newest to oldest
        """
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
