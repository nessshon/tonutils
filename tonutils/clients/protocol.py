from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from ton_core import (
        AddressLike,
        Cell,
        DNSCategory,
        DNSRecordDNSNextResolver,
        DNSRecordSite,
        DNSRecordStorage,
        DNSRecordText,
        DNSRecordWallet,
        NetworkGlobalID,
        Transaction,
    )

    from tonutils.types import (
        ClientType,
        ContractInfo,
    )


@t.runtime_checkable
class ClientProtocol(t.Protocol):
    """Unified interface for TON data providers.

    Defines the minimal set of operations supported by all client types.
    """

    TYPE: ClientType
    """Client implementation type (``HTTP`` or ``ADNL``)."""

    network: NetworkGlobalID
    """Network the client operates on."""

    @property
    def provider(self) -> t.Any:
        """Underlying provider or transport backend."""

    @property
    def connected(self) -> bool:
        """``True`` if the client is ready for requests."""

    async def send_message(self, boc: str) -> None:
        """Send an external message to the blockchain.

        :param boc: Hex-encoded BoC string.
        """

    async def get_config(self) -> dict[int, t.Any]:
        """Fetch global blockchain configuration.

        :return: Mapping of config parameter IDs to values.
        """

    async def get_info(self, address: AddressLike) -> ContractInfo:
        """Fetch contract state information.

        :param address: Contract address.
        :return: ``ContractInfo`` snapshot.
        """

    async def get_transactions(
        self,
        address: AddressLike,
        limit: int = 100,
        from_lt: int | None = None,
        to_lt: int | None = None,
    ) -> list[Transaction]:
        """Fetch contract transactions.

        :param address: Contract address.
        :param limit: Maximum transactions to return.
        :param from_lt: Upper-bound logical time filter.
        :param to_lt: Lower-bound logical time filter.
        :return: List of ``Transaction`` objects.
        """

    async def run_get_method(
        self,
        address: AddressLike,
        method_name: str,
        stack: list[t.Any] | None = None,
    ) -> list[t.Any]:
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
        domain: str | bytes,
        category: DNSCategory,
        dns_root_address: AddressLike | None = None,
    ) -> (
        Cell
        | DNSRecordDNSNextResolver
        | DNSRecordSite
        | DNSRecordStorage
        | DNSRecordText
        | DNSRecordWallet
        | None
    ):
        """Resolve a TON DNS record for a domain and category.

        :param domain: Domain name string or bytes.
        :param category: DNS record category to query.
        :param dns_root_address: Custom DNS root address, or ``None``.
        :return: Resolved DNS record, or ``None``.
        """
