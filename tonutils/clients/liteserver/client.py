from __future__ import annotations

import typing as t
from functools import wraps

from pytoniq_core import Address, SimpleAccount, Transaction

from ..base import BaseClient
from ...exceptions import PytoniqDependencyError
from ...types import (
    ContractStateInfo,
    ContractState,
    ClientType,
)
from ...utils import (
    StackCodec,
    cell_to_hex,
)

try:
    # noinspection PyPackageRequirements
    from pytoniq import LiteBalancer

    pytoniq_available = True
except ImportError:
    pytoniq_available = False
    from .stub import LiteBalancer

F = t.TypeVar("F", bound=t.Callable[..., t.Any])


def _ensure_api_ready(func: F) -> F:

    @wraps(func)
    async def wrapper(self: LiteserverClient, *args: t.Any, **kwargs: t.Any) -> t.Any:
        if not pytoniq_available:
            raise PytoniqDependencyError()
        if not self.api.inited:
            await self.api.start_up()
        return await func(self, *args, **kwargs)

    return t.cast(F, wrapper)


class LiteserverClient(BaseClient[LiteBalancer]):

    def __init__(
        self,
        config: t.Optional[t.Dict[str, t.Any]] = None,
        is_testnet: bool = False,
        trust_level: int = 2,
    ) -> None:
        if not pytoniq_available:
            raise PytoniqDependencyError()

        if config is not None:
            self.api = LiteBalancer.from_config(config, trust_level)
        elif is_testnet:
            self.api = LiteBalancer.from_testnet_config(trust_level)
        else:
            self.api = LiteBalancer.from_mainnet_config(trust_level)

        self.is_testnet = is_testnet

    async def __aenter__(self) -> LiteBalancer:
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
        await self.api.raw_send_message(bytes.fromhex(boc))

    @_ensure_api_ready
    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        return await self.api.get_config_all()

    @_ensure_api_ready
    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        account, shard_account = await self.api.raw_get_account_state(address)

        simple_account = SimpleAccount.from_raw(account, Address(address))
        contract_info = ContractStateInfo(balance=simple_account.balance)

        if simple_account.state is not None:
            state_init = simple_account.state.state_init
            if state_init is not None:
                if state_init.code is not None:
                    contract_info.code_raw = cell_to_hex(state_init.code)
                if state_init.data is not None:
                    contract_info.data_raw = cell_to_hex(state_init.data)

            contract_info.state = ContractState(
                "uninit"
                if simple_account.state.type_ == "uninitialized"
                else simple_account.state.type_
            )

        if shard_account is not None:
            if shard_account.last_trans_lt is not None:
                contract_info.last_transaction_lt = int(shard_account.last_trans_lt)
            if shard_account.last_trans_hash is not None:
                contract_info.last_transaction_hash = (
                    shard_account.last_trans_hash.hex()
                )
        if (
            contract_info.last_transaction_lt is None
            and contract_info.last_transaction_hash is None
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
        return await self.api.get_transactions(
            address=Address(address),
            count=limit,
            from_lt=from_lt,
            to_lt=to_lt,
        )

    @_ensure_api_ready
    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        stack_codec = StackCodec(ClientType.LITESERVER)
        stack_result = await self.api.run_get_method(
            address=address,
            method=method_name,
            stack=stack_codec.encode(stack or []),
        )
        return stack_codec.decode(stack_result or [])

    async def startup(self) -> None:
        await self.api.start_up()

    async def close(self) -> None:
        await self.api.close_all()
