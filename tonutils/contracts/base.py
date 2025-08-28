from __future__ import annotations

import typing as t

from pyapiq.exceptions import APIQException
from pytoniq_core import Address, Cell, StateInit

from .codes import CONTRACT_CODES
from ..exceptions import NotRefreshedError
from ..protocols import (
    ClientProtocol,
    ContractProtocol,
)
from ..types import (
    ContractStateInfo,
    WorkchainID,
    AddressLike,
    ContractState,
    BaseContractVersion,
    BaseContractData,
)
from ..utils import to_cell

D = t.TypeVar("D", bound=BaseContractData)

TContract = t.TypeVar("TContract", bound="BaseContract")


class BaseContract(ContractProtocol[D]):
    _data_model: t.Type[D]

    VERSION: t.ClassVar[BaseContractVersion]

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
    def state_init(self) -> StateInit:
        return self._state_init

    @property
    def state_info(self) -> ContractStateInfo:
        if self._state_info is None:
            raise NotRefreshedError(self, "state_info")
        return t.cast(ContractStateInfo, self._state_info)

    @property
    def state_data(self) -> D:
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
    def code(self) -> t.Optional[Cell]:
        return self.state_info.code

    @property
    def data(self) -> t.Optional[Cell]:
        return self.state_info.data

    async def refresh(self) -> None:
        try:
            state_info = await self.client.get_contract_info(self.address)
        except APIQException:
            state_info = ContractStateInfo()
        self._state_info = state_info

    @classmethod
    def from_state_init(
        cls: t.Type[TContract],
        client: ClientProtocol,
        state_init: StateInit,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> TContract:
        address = Address((workchain.value, state_init.serialize().hash))
        return cls(client=client, address=address, state_init=state_init)

    @classmethod
    def from_code_and_data(
        cls: t.Type[TContract],
        client: ClientProtocol,
        code: Cell,
        data: Cell,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> TContract:
        state_init = StateInit(code=code, data=data)
        return cls.from_state_init(client, state_init, workchain)

    @classmethod
    def from_data(
        cls: t.Type[TContract],
        client: ClientProtocol,
        data: Cell,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> TContract:
        code = to_cell(CONTRACT_CODES[cls.VERSION])
        return cls.from_code_and_data(client, code, data, workchain)

    @classmethod
    async def from_address(
        cls: t.Type[TContract],
        client: ClientProtocol,
        address: AddressLike,
    ) -> TContract:
        try:
            state_info = await client.get_contract_info(address)
        except APIQException:
            state_info = ContractStateInfo()
        return cls(
            client=client,
            address=address,
            state_info=state_info,
        )
