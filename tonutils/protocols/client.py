from __future__ import annotations

import typing as t

from pytoniq_core import Transaction

from ..types import AddressLike, ContractStateInfo


@t.runtime_checkable
class ClientProtocol(t.Protocol):
    is_testnet: bool
    api: t.Any

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
        to_lt: t.Optional[int] = 0,
    ) -> t.List[Transaction]: ...

    async def run_get_method(
        self,
        address: AddressLike,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]: ...

    async def startup(self) -> None: ...

    async def close(self) -> None: ...
