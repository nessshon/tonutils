from __future__ import annotations

import typing as t

from pytoniq_core import Cell, Transaction

from tonutils.types import (
    AddressLike,
    ContractInfo,
    DNSCategory,
    NetworkGlobalID,
    ClientType,
)

if t.TYPE_CHECKING:
    from tonutils.contracts.dns.tlb import (
        DNSRecordDNSNextResolver,
        DNSRecordWallet,
        DNSRecordStorage,
        DNSRecordSite,
    )


@t.runtime_checkable
class ClientProtocol(t.Protocol):
    """Unified interface for TON data providers.

    Defines the minimal set of operations supported by all client types.
    """

    TYPE: ClientType
    """Client implementation type (`HTTP` or `ADNL`)."""

    network: NetworkGlobalID
    """Network the client operates on (`MAINNET` or `TESTNET`)."""

    @property
    def provider(self) -> t.Any:
        """Underlying provider or transport backend."""

    @property
    def connected(self) -> bool:
        """`True` if the client is ready for requests."""

    async def send_message(self, boc: str) -> None:
        """Send an external message to the blockchain.

        :param boc: Hex-encoded BoC string.
        """

    async def get_config(self) -> t.Dict[int, t.Any]:
        """Fetch global blockchain configuration.

        :return: Mapping of config parameter IDs to values.
        """

    async def get_info(self, address: AddressLike) -> ContractInfo:
        """Fetch contract state information.

        :param address: Contract address.
        :return: `ContractInfo` snapshot.
        """

    async def get_transactions(
        self,
        address: AddressLike,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = None,
    ) -> t.List[Transaction]:
        """Fetch contract transactions.

        :param address: Contract address.
        :param limit: Maximum transactions to return.
        :param from_lt: Upper-bound logical time filter.
        :param to_lt: Lower-bound logical time filter.
        :return: List of `Transaction` objects.
        """

    async def run_get_method(
        self,
        address: AddressLike,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        """Execute a contract get-method.

        :param address: Contract address.
        :param method_name: Name of the get-method.
        :param stack: TVM stack arguments.
        :return: Decoded TVM stack result.
        """

    async def connect(self) -> None:
        """Establish connection and initialize resources."""

    async def close(self) -> None:
        """Close connection and release resources."""

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
        """Resolve a TON DNS record for a domain and category.

        :param domain: Domain name string or bytes.
        :param category: DNS record category to query.
        :param dns_root_address: Custom DNS root address, or `None`.
        :return: Resolved DNS record, or `None`.
        """
