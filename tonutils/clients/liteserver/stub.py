from __future__ import annotations

import typing as t
from types import TracebackType

from pytoniq_core import Address, Transaction

from ...exceptions import PytoniqDependencyError


class LiteBalancer:
    inited: bool = False

    @staticmethod
    def from_config(
        config: t.Dict[str, t.Any],
        trust_level: int,
    ) -> LiteBalancer:
        raise PytoniqDependencyError()

    @staticmethod
    def from_testnet_config(trust_level: int) -> LiteBalancer:
        raise PytoniqDependencyError()

    @staticmethod
    def from_mainnet_config(trust_level: int) -> LiteBalancer:
        raise PytoniqDependencyError()

    async def __aenter__(self) -> LiteBalancer:
        raise PytoniqDependencyError()

    async def __aexit__(
        self,
        exc_type: t.Optional[type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[TracebackType],
    ) -> None:
        raise PytoniqDependencyError()

    async def run_get_method(
        self,
        address: t.Union[str, Address],
        method: str,
        stack: t.List[t.Any],
    ) -> t.Any:
        raise PytoniqDependencyError()

    async def raw_send_message(self, message: bytes) -> None:
        raise PytoniqDependencyError()

    async def start_up(self):
        raise PytoniqDependencyError()

    async def close_all(self):
        raise PytoniqDependencyError()

    async def raw_get_account_state(self, address):
        raise PytoniqDependencyError()

    async def get_config_all(self) -> t.Dict[int, t.Any]:
        raise PytoniqDependencyError()

    async def get_transactions(
        self,
        address: t.Union[str, Address],
        count: int,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]:
        raise PytoniqDependencyError()
