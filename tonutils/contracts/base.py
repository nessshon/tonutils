from __future__ import annotations

import typing as t

from pytoniq_core import Address, Cell, StateInit, TlbScheme

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.codes import CONTRACT_CODES
from tonutils.contracts.protocol import ContractProtocol
from tonutils.contracts.versions import ContractVersion
from tonutils.exceptions import (
    ContractError,
    StateNotLoadedError,
    ProviderResponseError,
)
from tonutils.types import AddressLike, ContractInfo, ContractState, WorkchainID
from tonutils.utils import to_cell

_R = t.TypeVar("_R")
_D = t.TypeVar("_D", bound=TlbScheme)

_TContract = t.TypeVar("_TContract", bound="BaseContract")


class BaseContract(ContractProtocol[_D]):
    """Base implementation for TON smart contract wrappers."""

    _data_model: t.Type[_D]
    VERSION: t.ClassVar[t.Union[ContractVersion, str]]

    @classmethod
    def get_default_code(cls) -> Cell:
        """Return default compiled code `Cell` for this contract version."""
        try:
            default_code = to_cell(CONTRACT_CODES[cls.VERSION])
        except KeyError:
            raise ContractError(
                cls, f"No contract code defined for `version` {cls.VERSION!r}."
            )
        return default_code

    def __init__(
        self,
        client: ClientProtocol,
        address: Address,
        state_init: t.Optional[StateInit] = None,
        info: t.Optional[ContractInfo] = None,
    ) -> None:
        """
        :param client: TON client.
        :param address: Contract address.
        :param state_init: Known code and data, or `None`.
        :param info: Preloaded on-chain state, or `None`.
        """
        self._client = client
        self._address = address
        self._state_init = state_init
        self._info = info

    @property
    def client(self) -> ClientProtocol:
        """TON client bound to this contract."""
        return self._client

    @property
    def address(self) -> Address:
        """Address of this contract."""
        return self._address

    @property
    def state_init(self) -> t.Optional[StateInit]:
        """Locally known `StateInit`, or `None`."""
        return self._state_init

    @property
    def state_data(self) -> _D:
        """Decoded on-chain data in typed form."""
        if not hasattr(self, "_data_model") or self._data_model is None:
            raise ContractError(self, "No `_data_model` defined for contract class.")
        if not (self._info and self._info.data):
            raise StateNotLoadedError(self, missing="state_data")
        cs = self._info.data.begin_parse()
        return self._data_model.deserialize(cs)

    @property
    def info(self) -> ContractInfo:
        """Cached on-chain state snapshot."""
        if self._info is None:
            raise StateNotLoadedError(self, missing="info")
        return t.cast(ContractInfo, self._info)

    @property
    def balance(self) -> int:
        """Contract balance in nanotons."""
        return self.info.balance

    @property
    def state(self) -> ContractState:
        """Current lifecycle state."""
        return self.info.state

    @property
    def is_active(self) -> bool:
        """`True` if state is `ACTIVE`."""
        return self.state == ContractState.ACTIVE

    @property
    def is_frozen(self) -> bool:
        """`True` if state is `FROZEN`."""
        return self.state == ContractState.FROZEN

    @property
    def is_uninit(self) -> bool:
        """`True` if state is `UNINIT`."""
        return self.state == ContractState.UNINIT

    @property
    def is_nonexit(self) -> bool:
        """`True` if state is `NONEXIST`."""
        return self.state == ContractState.NONEXIST

    @property
    def last_transaction_lt(self) -> t.Optional[int]:
        """Logical time of the last transaction, or `None`."""
        return self.info.last_transaction_lt

    @property
    def last_transaction_hash(self) -> t.Optional[str]:
        """Hash of the last transaction as hex string, or `None`."""
        return self.info.last_transaction_hash

    @property
    def code(self) -> t.Optional[Cell]:
        """Contract code `Cell`, or `None`."""
        return self.info.code

    @property
    def data(self) -> t.Optional[Cell]:
        """Contract data `Cell`, or `None`."""
        return self.info.data

    @classmethod
    async def _load_info(
        cls,
        client: ClientProtocol,
        address: Address,
    ) -> ContractInfo:
        """Fetch contract state, returning default on failure."""
        try:
            return await client.get_info(address)
        except ProviderResponseError as e:
            if e.code in {429, 228, 5556}:
                raise
            return ContractInfo()
        except (Exception,):
            return ContractInfo()

    async def refresh(self) -> None:
        """Refresh contract state from the blockchain."""
        self._info = await self._load_info(self.client, self.address)

    @classmethod
    def from_state_init(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        state_init: StateInit,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract:
        """Construct from a `StateInit`.

        :param client: TON client.
        :param state_init: `StateInit` containing code and data.
        :param workchain: Target workchain.
        :return: New contract instance.
        """
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
        """Construct from code and data cells.

        :param client: TON client.
        :param code: Contract code cell.
        :param data: Contract data cell.
        :param workchain: Target workchain.
        :return: New contract instance.
        """
        state_init = StateInit(code=code, data=data)
        return cls.from_state_init(client, state_init, workchain)

    @classmethod
    def from_data(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        data: Cell,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract:
        """Construct from a data cell using default code.

        :param client: TON client.
        :param data: Contract data cell.
        :param workchain: Target workchain.
        :return: New contract instance.
        """
        code = cls.get_default_code()
        return cls.from_code_and_data(client, code, data, workchain)

    @classmethod
    async def from_address(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        address: AddressLike,
        load_state: bool = True,
    ) -> _TContract:
        """Construct from an on-chain address.

        :param client: TON client.
        :param address: Deployed contract address.
        :param load_state: Fetch current state from the blockchain.
        :return: Contract instance bound to the address.
        """
        if isinstance(address, str):
            address = Address(address)
        if not load_state:
            return cls(client, address)

        info = await cls._load_info(client, address)
        return cls(client, address, info=info)

    def __repr__(self) -> str:
        return f"< Contract {self.__class__.__name__} address: {self.address} >"
