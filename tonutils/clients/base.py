import abc
import typing as t

from pyapiq import AsyncClientAPI
from pytoniq_core import Address, Transaction

from .liteserver.stub import LiteBalancer
from ..types import AddressLike, ContractStateInfo

A = t.TypeVar("A", bound=t.Union[AsyncClientAPI, LiteBalancer])


class BaseClient(abc.ABC, t.Generic[A]):
    is_testnet: bool
    api: A

    @abc.abstractmethod
    async def _send_boc(self, boc: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        raise NotImplementedError

    @abc.abstractmethod
    async def _get_contract_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = 0,
    ) -> t.List[Transaction]:
        raise NotImplementedError

    @abc.abstractmethod
    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        raise NotImplementedError

    @abc.abstractmethod
    async def startup(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

    async def send_boc(self, boc: str) -> None:
        await self._send_boc(boc)

    async def get_blockchain_config(self) -> t.Dict[int, t.Any]:
        return await self._get_blockchain_config()

    async def get_contract_info(self, address: AddressLike) -> ContractStateInfo:
        if isinstance(address, Address):
            address = Address(address).to_str(is_user_friendly=False)
        return await self._get_contract_info(address=address)

    async def get_contract_transactions(
        self,
        address: AddressLike,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = 0,
    ) -> t.List[Transaction]:
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
        if isinstance(address, Address):
            address = Address(address).to_str(is_user_friendly=False)
        return await self._run_get_method(
            address=address,
            method_name=method_name,
            stack=stack,
        )
