from __future__ import annotations

import base64
import binascii
import typing as t
from functools import wraps

from pyapiq import AsyncClientAPI
from pytoniq_core import Transaction, Cell, Slice

from .api import ToncenterAPI
from .models import (
    SendBocPayload,
    RunGetMethodPayload,
)
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


def _norm_lt(v: t.Any) -> t.Optional[int]:
    try:
        iv = int(v)
    except (TypeError, ValueError):
        return None
    return iv or None


def _norm_b64_hash_to_hex(b64s: t.Optional[str]) -> t.Optional[str]:
    if not b64s:
        return None
    try:
        h = base64.b64decode(b64s).hex()
    except (binascii.Error, ValueError):
        return None
    return None if h == bytes(32).hex() else h


def _ensure_api_ready(func: F) -> F:

    @wraps(func)
    async def wrapper(self: ToncenterClient, *args: t.Any, **kwargs: t.Any) -> t.Any:
        if self.api.session is None:
            await self.api.ensure_session()
        return await func(self, *args, **kwargs)

    return t.cast(F, wrapper)


class ToncenterClient(BaseClient[ToncenterAPI]):

    def __init__(
        self,
        api_key: t.Optional[str] = None,
        is_testnet: bool = False,
        base_url: t.Optional[str] = None,
        rps: t.Optional[int] = None,
        max_retries: int = 2,
    ) -> None:
        self.is_testnet = is_testnet
        self.api = ToncenterAPI(
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
        payload = SendBocPayload(boc=boc)
        return await self.api.send_boc(payload=payload)

    @_ensure_api_ready
    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        request = await self.api.get_config_all()

        if request.result is None:
            raise ClientError(
                "Invalid get_config_all response: missing 'result' field."
            )

        if request.result.config is None:
            raise ClientError(
                "Invalid config response: missing 'config' section in result."
            )

        if request.result.config.bytes is None:
            raise ClientError(
                "Invalid config response: missing 'bytes' field in 'config' section."
            )

        config_cell = Cell.one_from_boc(request.result.config.bytes)
        config_slice = config_cell.begin_parse()
        return parse_config(config_slice)

    @_ensure_api_ready
    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        request = await self.api.get_address_information(address)

        contract_info = ContractStateInfo(
            balance=int(request.result.balance),
            state=ContractState(request.result.state),
        )
        if bool(request.result.code):
            contract_info.code_raw = cell_to_hex(request.result.code)

        if bool(request.result.data):
            contract_info.data_raw = cell_to_hex(request.result.data)

        last_transaction_lt = last_transaction_hash = None
        if request.result.last_transaction_id:
            last_transaction_lt = _norm_lt(request.result.last_transaction_id.lt)
            last_transaction_hash = _norm_b64_hash_to_hex(
                request.result.last_transaction_id.hash
            )

        contract_info.last_transaction_lt = last_transaction_lt
        contract_info.last_transaction_hash = last_transaction_hash

        if (
            last_transaction_lt is None
            and last_transaction_hash is None
            and contract_info.state == ContractState.UNINIT
        ):
            contract_info.state = ContractState.NONEXIST

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

        request = await self.api.get_transaction(
            address=address,
            limit=limit,
            from_lt=from_lt,
            to_lt=to_lt,
        )

        transactions = []
        for tx in request.result or []:
            if tx.data is not None:
                tx_slice = Slice.one_from_boc(tx.data)
                transactions.append(Transaction.deserialize(tx_slice))

        return transactions

    @_ensure_api_ready
    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        stack_codec = StackCodec(ClientType.TONCENTER)
        payload = RunGetMethodPayload(
            address=address,
            method=method_name,
            stack=stack_codec.encode(stack or []),
        )
        request = await self.api.run_get_method(payload=payload)
        if request.result is None:
            return []
        return stack_codec.decode(request.result.stack or [])

    async def startup(self) -> None:
        await self.api.ensure_session()

    async def close(self) -> None:
        await self.api.close()
