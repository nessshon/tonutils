from __future__ import annotations

import typing as t

from pyapiq.exceptions import APIQException, RateLimitExceeded
from pytoniq_core import Address, Cell, StateInit, TlbScheme

from tonutils.contracts.codes import CONTRACT_CODES
from tonutils.contracts.versions import ContractVersion
from tonutils.exceptions import ContractError, NotRefreshedError
from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import WorkchainID, AddressLike, ContractState, ContractStateInfo
from tonutils.utils import to_cell

_R = t.TypeVar("_R")
_D = t.TypeVar("_D", bound=TlbScheme)

_TContract = t.TypeVar("_TContract", bound="BaseContract")


class BaseContract(ContractProtocol[_D]):
    _data_model: t.Type[_D]
    VERSION: t.ClassVar[t.Union[ContractVersion, str]]

    @classmethod
    def get_default_code(cls) -> Cell:
        try:
            default_code = to_cell(CONTRACT_CODES[cls.VERSION])
        except KeyError:
            raise ContractError(
                cls, f"No contract code defined for `VERSION` {cls.VERSION!r}."
            )
        return default_code

    def __init__(
        self,
        client: ClientProtocol,
        address: Address,
        state_init: t.Optional[StateInit] = None,
        state_info: t.Optional[ContractStateInfo] = None,
    ) -> None:
        self._client = client
        self._address = address
        self._state_init = state_init
        self._state_info = state_info

    @property
    def client(self) -> ClientProtocol:
        return self._client

    @property
    def address(self) -> Address:
        return self._address

    @property
    def state_init(self) -> t.Optional[StateInit]:
        return self._state_init

    @property
    def state_info(self) -> ContractStateInfo:
        if self._state_info is None:
            raise NotRefreshedError(self, "state_info")
        return t.cast(ContractStateInfo, self._state_info)

    @property
    def state_data(self) -> _D:
        if not hasattr(self, "_data_model") or self._data_model is None:
            raise ContractError(self, "No `_data_model` defined for contract class.")
        if not (self._state_info and self._state_info.data):
            raise NotRefreshedError(self, "state_data")
        cs = self._state_info.data.begin_parse()
        return self._data_model.deserialize(cs)

    @property
    def balance(self) -> int:
        return self.state_info.balance

    @property
    def state(self) -> ContractState:
        return self.state_info.state

    @property
    def is_active(self) -> bool:
        return self.state == ContractState.ACTIVE

    @property
    def is_frozen(self) -> bool:
        return self.state == ContractState.FROZEN

    @property
    def is_uninit(self) -> bool:
        return self.state == ContractState.UNINIT

    @property
    def is_nonexit(self) -> bool:
        return self.state == ContractState.NONEXIST

    @property
    def last_transaction_lt(self) -> t.Optional[int]:
        return self.state_info.last_transaction_lt

    @property
    def last_transaction_hash(self) -> t.Optional[str]:
        return self.state_info.last_transaction_hash

    @property
    def code(self) -> t.Optional[Cell]:
        return self.state_info.code

    @property
    def data(self) -> t.Optional[Cell]:
        return self.state_info.data

    async def refresh(self) -> None:
        try:
            state_info = await self.client.get_contract_info(self.address)
        except RateLimitExceeded:
            raise
        except APIQException:
            state_info = ContractStateInfo()
        self._state_info = state_info

    @classmethod
    def from_state_init(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        state_init: StateInit,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract:
        address = Address((workchain.value, state_init.serialize().hash))
        return cls(client=client, address=address, state_init=state_init)

    @classmethod
    def from_code_and_data(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        code: Cell,
        data: Cell,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract:
        state_init = StateInit(code=code, data=data)
        return cls.from_state_init(client, state_init, workchain)

    @classmethod
    def from_data(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        data: Cell,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract:
        code = cls.get_default_code()
        return cls.from_code_and_data(client, code, data, workchain)

    @classmethod
    async def from_address(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        address: AddressLike,
        load_state: bool = True,
    ) -> _TContract:
        if isinstance(address, str):
            address = Address(address)
        if not load_state:
            return cls(client, address)
        try:
            state_info = await client.get_contract_info(address)
        except RateLimitExceeded:
            raise
        except APIQException:
            state_info = ContractStateInfo()
        return cls(client, address, state_info=state_info)

    def __repr__(self) -> str:
        return f"< Contract {self.__class__.__name__} address: {self.address} >"
