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
    TYPE: ClientType
    network: NetworkGlobalID

    @property
    def provider(self) -> t.Any: ...

    @property
    def is_connected(self) -> bool: ...

    async def send_boc(self, boc: str) -> None: ...

    async def get_blockchain_config(self) -> t.Dict[int, t.Any]: ...

    async def get_contract_info(
        self,
        address: AddressLike,
    ) -> ContractStateInfo: ...

    async def get_contract_transactions(
        self,
        address: AddressLike,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]: ...

    async def run_get_method(
        self,
        address: AddressLike,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]: ...

    async def connect(self) -> None: ...

    async def close(self) -> None: ...

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
    ]: ...
