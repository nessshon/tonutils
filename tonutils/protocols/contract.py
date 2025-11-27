from __future__ import annotations

import typing as t

from pytoniq_core import Address, Cell, StateInit

from tonutils.protocols.client import ClientProtocol
from tonutils.types import AddressLike, ContractState, ContractStateInfo, WorkchainID

if t.TYPE_CHECKING:
    from tonutils.contracts.versions import ContractVersion

_D = t.TypeVar("_D")

_TContract = t.TypeVar("_TContract")


@t.runtime_checkable
class ContractProtocol(t.Protocol[_D]):
    _data_model: t.Type[_D]

    VERSION: t.ClassVar[t.Union[ContractVersion, str]]

    @classmethod
    def get_default_code(cls) -> Cell: ...

    @property
    def client(self) -> ClientProtocol: ...

    @property
    def address(self) -> Address: ...

    @property
    def state_init(self) -> t.Optional[StateInit]: ...

    @property
    def state_info(self) -> ContractStateInfo: ...

    @property
    def state_data(self) -> _D: ...

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
    def last_transaction_lt(self) -> t.Optional[int]: ...

    @property
    def last_transaction_hash(self) -> t.Optional[str]: ...

    @property
    def code(self) -> Cell: ...

    @property
    def data(self) -> Cell: ...

    async def refresh(self) -> None: ...

    @classmethod
    def from_state_init(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        state_init: StateInit,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract: ...

    @classmethod
    def from_code_and_data(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        code: Cell,
        data: Cell,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract: ...

    @classmethod
    def from_data(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        data: _D,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract: ...

    @classmethod
    async def from_address(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        address: AddressLike,
        load_state: bool = True,
    ) -> _TContract: ...
