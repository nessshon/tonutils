from __future__ import annotations

import typing as t
from functools import wraps

from pyapiq import AsyncClientAPI
from pytoniq_core import Cell, Slice, Transaction

from .api import TonapiAPI
from .models import BlockchainMessagePayload
from ..base import BaseClient
from ...exceptions import ClientError
from ...types import (
    ContractStateInfo,
    ContractState,
    ClientType,
)
from ...utils import (
    StackCodec,
    cell_to_hex,
    parse_config,
)

F = t.TypeVar("F", bound=t.Callable[..., t.Any])


def _ensure_api_ready(func: F) -> F:

    @wraps(func)
    async def wrapper(self: "TonapiClient", *args: t.Any, **kwargs: t.Any) -> t.Any:
        if self.api.session is None:
            await self.api.ensure_session()
        return await func(self, *args, **kwargs)

    return t.cast(F, wrapper)


class TonapiClient(BaseClient[TonapiAPI]):

    def __init__(
        self,
        api_key: str,
        is_testnet: bool = False,
        base_url: t.Optional[str] = None,
        rps: t.Optional[int] = None,
        max_retries: int = 2,
    ) -> None:
        self.is_testnet = is_testnet
        self.api = TonapiAPI(
            api_key=api_key,
            is_testnet=is_testnet,
            base_url=base_url,
            rps=rps,
            max_retries=max_retries,
        )

    async def __aenter__(self) -> AsyncClientAPI:
        return await self.api.__aenter__()

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        await self.api.__aexit__(exc_type, exc_value, traceback)

    @_ensure_api_ready
    async def _send_boc(self, boc: str) -> None:
        payload = BlockchainMessagePayload(boc=boc)
        return await self.api.blockchain_message(payload=payload)

    @_ensure_api_ready
    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        result = await self.api.blockchain_config()

        if result.raw is None:
            raise ClientError("Invalid config response: missing 'raw' field")

        config_cell = Cell.one_from_boc(result.raw)[0]
        config_slice = config_cell.begin_parse()
        return parse_config(config_slice)

    @_ensure_api_ready
    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        result = await self.api.blockchain_account(address)

        contract_info = ContractStateInfo(
            balance=result.balance,
            state=ContractState(result.status),
            last_transaction_lt=result.last_transaction_lt,
            last_transaction_hash=result.last_transaction_hash,
        )
        if result.code is not None:
            contract_info.code_raw = cell_to_hex(result.code)
        if result.data is not None:
            contract_info.data_raw = cell_to_hex(result.data)

        return contract_info

    @_ensure_api_ready
    async def _get_contract_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = 0,
    ) -> t.List[Transaction]:
        if from_lt is not None:
            from_lt += 1

        result = await self.api.blockchain_account_transactions(
            address=address,
            limit=limit,
            after_lt=to_lt,
            before_lt=from_lt,
        )

        transactions = []
        for tx in result.transactions or []:
            if tx.raw is not None:
                tx_slice = Slice.one_from_boc(tx.raw)
                transactions.append(Transaction.deserialize(tx_slice))

        return transactions

    @_ensure_api_ready
    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        stack_codec = StackCodec(ClientType.TONAPI)
        result = await self.api.blockchain_account_method(
            address=address,
            method_name=method_name,
            args=stack_codec.encode(stack or []),
        )
        return stack_codec.decode(result.stack or [])

    async def startup(self) -> None:
        await self.api.ensure_session()

    async def close(self) -> None:
        await self.api.close()
