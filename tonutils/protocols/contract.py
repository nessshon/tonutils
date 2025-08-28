from __future__ import annotations

import typing as t

from pytoniq_core import Address, Cell, StateInit

from .client import ClientProtocol
from ..types import (
    BaseContractVersion,
    AddressLike,
    WorkchainID,
    ContractState,
    ContractStateInfo,
)

D = t.TypeVar("D")

TContract = t.TypeVar("TContract")


@t.runtime_checkable
class ContractProtocol(t.Protocol[D]):
    _data_model: t.Type[D]

    VERSION: t.ClassVar[BaseContractVersion]

    @property
    def client(self) -> ClientProtocol: ...

    @property
    def address(self) -> Address: ...

    @property
    def state_init(self) -> StateInit: ...

    @property
    def state_info(self) -> ContractStateInfo: ...

    @property
    def state_data(self) -> D: ...

    @property
    def balance(self) -> int:
        return self.state_info.balance

    @property
    def state(self) -> ContractState: ...

    @property
    def is_active(self) -> bool: ...

    @property
    def is_frozen(self) -> bool: ...

    @property
    def is_uninit(self) -> bool: ...

    @property
    def is_nonexit(self) -> bool: ...

    @property
    def code(self) -> Cell: ...

    @property
    def data(self) -> Cell: ...

    async def refresh(self) -> None: ...

    @classmethod
    def from_state_init(
        cls: t.Type[TContract],
        client: ClientProtocol,
        state_init: StateInit,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> TContract: ...

    @classmethod
    def from_code_and_data(
        cls: t.Type[TContract],
        client: ClientProtocol,
        code: Cell,
        data: Cell,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> TContract: ...

    @classmethod
    def from_data(
        cls: t.Type[TContract],
        client: ClientProtocol,
        data: D,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> TContract: ...

    @classmethod
    async def from_address(
        cls: t.Type[TContract],
        client: ClientProtocol,
        address: AddressLike,
    ) -> TContract: ...
