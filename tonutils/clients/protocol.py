from __future__ import annotations

import typing as t

from pytoniq_core import Cell, Transaction

from tonutils.types import (
    AddressLike,
    ContractStateInfo,
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
    """
    Unified interface for TON data providers.

    Defines the minimal set of operations supported by all client types.
    """

    TYPE: ClientType
    """Type of the underlying client implementation (HTTP or ADNL)."""

    network: NetworkGlobalID
    """Global network identifier the client is operating on (MAINNET or TESTNET)."""

    @property
    def provider(self) -> t.Any:
        """Underlying provider or transport backend."""

    @property
    def is_connected(self) -> bool:
        """Whether the client is connected and ready for requests."""

    async def send_boc(self, boc: str) -> None:
        """Send an external message to the blockchain."""

    async def get_blockchain_config(self) -> t.Dict[int, t.Any]:
        """Fetch global blockchain configuration."""

    async def get_contract_info(
        self,
        address: AddressLike,
    ) -> ContractStateInfo:
        """Fetch basic contract state information."""

    async def get_contract_transactions(
        self,
        address: AddressLike,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]:
        """Fetch contract transactions."""

    async def run_get_method(
        self,
        address: AddressLike,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        """Execute a contract get-method and return resulting stack values."""

    async def connect(self) -> None:
        """Establish connection and initialize provider resources."""

    async def close(self) -> None:
        """Close connection and release provider resources."""

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
        """Resolve a TON DNS record for a domain and category."""
