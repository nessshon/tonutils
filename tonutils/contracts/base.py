from __future__ import annotations

import typing as t

from pyapiq.exceptions import APIQException, RateLimitExceeded
from pytoniq_core import Address, Cell, StateInit, TlbScheme

from tonutils.contracts.codes import CONTRACT_CODES
from tonutils.contracts.versions import ContractVersion
from tonutils.exceptions import ContractError, NotRefreshedError
from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike, ContractState, ContractStateInfo, WorkchainID
from tonutils.utils import to_cell

_R = t.TypeVar("_R")
_D = t.TypeVar("_D", bound=TlbScheme)

_TContract = t.TypeVar("_TContract", bound="BaseContract")


class BaseContract(ContractProtocol[_D]):
    """
    Base implementation for TON smart contract wrappers.

    Provides common functionality for interacting with TON smart contracts,
    including state management, address resolution, and factory methods for
    constructing contract instances from various sources.

    Subclasses must define:
      - _data_model: TlbScheme class for deserializing contract data
      - VERSION: Contract version key for code lookup
    """

    _data_model: t.Type[_D]
    VERSION: t.ClassVar[t.Union[ContractVersion, str]]

    @classmethod
    def get_default_code(cls) -> Cell:
        """
        Return default contract code for the current VERSION.

        Looks up the compiled code in the global CONTRACT_CODES registry and
        converts it into a Cell instance.

        :return: Default contract code cell for this contract class
        """
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
        """
        Initialize base contract wrapper.

        :param client: TON client for blockchain interactions
        :param address: Contract address on the blockchain
        :param state_init: Optional known StateInit (code and data)
        :param state_info: Optional preloaded on-chain contract state
        """
        self._client = client
        self._address = address
        self._state_init = state_init
        self._state_info = state_info

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
        """Locally known StateInit for this contract, if any."""
        return self._state_init

    @property
    def state_info(self) -> ContractStateInfo:
        """
        Cached snapshot of the contract state.

        :return: Contract state information
        """
        if self._state_info is None:
            raise NotRefreshedError(self, "state_info")
        return t.cast(ContractStateInfo, self._state_info)

    @property
    def state_data(self) -> _D:
        """
        Decoded on-chain data in typed form.

        Deserializes the contract data cell using the _data_model TlbScheme.

        :return: Typed data object
        """
        if not hasattr(self, "_data_model") or self._data_model is None:
            raise ContractError(self, "No `_data_model` defined for contract class.")
        if not (self._state_info and self._state_info.data):
            raise NotRefreshedError(self, "state_data")
        cs = self._state_info.data.begin_parse()
        return self._data_model.deserialize(cs)

    @property
    def balance(self) -> int:
        """
        Current contract balance in nanotons.

        :return: Balance from the latest known state
        """
        return self.state_info.balance

    @property
    def state(self) -> ContractState:
        """
        Current lifecycle state of the contract.

        :return: One of ContractState enum values (ACTIVE, FROZEN, UNINIT, NONEXIST)
        """
        return self.state_info.state

    @property
    def is_active(self) -> bool:
        """
        Check whether the contract is active.

        :return: True if state is ACTIVE
        """
        return self.state == ContractState.ACTIVE

    @property
    def is_frozen(self) -> bool:
        """
        Check whether the contract is frozen.

        :return: True if state is FROZEN
        """
        return self.state == ContractState.FROZEN

    @property
    def is_uninit(self) -> bool:
        """
        Check whether the contract is uninitialized.

        :return: True if state is UNINIT
        """
        return self.state == ContractState.UNINIT

    @property
    def is_nonexit(self) -> bool:
        """
        Check whether the contract does not exist on-chain.

        :return: True if state is NONEXIST
        """
        return self.state == ContractState.NONEXIST

    @property
    def last_transaction_lt(self) -> t.Optional[int]:
        """
        Logical time of the last known transaction for this contract.

        :return: Transaction LT or None if unknown
        """
        return self.state_info.last_transaction_lt

    @property
    def last_transaction_hash(self) -> t.Optional[str]:
        """
        Hash of the last known transaction for this contract.

        :return: Transaction hash as hex string or None if unknown
        """
        return self.state_info.last_transaction_hash

    @property
    def code(self) -> t.Optional[Cell]:
        """
        Contract code cell from the latest known state.

        :return: Code cell or None if not available
        """
        return self.state_info.code

    @property
    def data(self) -> t.Optional[Cell]:
        """
        Contract data cell from the latest known state.

        :return: Data cell or None if not available
        """
        return self.state_info.data

    async def refresh(self) -> None:
        """
        Refresh contract state from the blockchain.

        Fetches current contract information and updates the cached state_info.
        If the request fails (except rate limits), sets state to default empty state.
        """
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
        """
        Construct a contract wrapper from a StateInit object.

        Derives the contract address from the StateInit hash.

        :param client: TON client to bind to the contract
        :param state_init: StateInit containing code and data
        :param workchain: Target workchain (default: BASECHAIN)
        :return: New contract instance
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
        """
        Construct a contract wrapper from code and data cells.

        Composes a StateInit from the provided cells and delegates to from_state_init().

        :param client: TON client to bind to the contract
        :param code: Contract code cell
        :param data: Contract data cell
        :param workchain: Target workchain (default: BASECHAIN)
        :return: New contract instance
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
        """
        Construct a contract wrapper from a data cell.

        Uses the default code from get_default_code() and combines it with
        the provided data cell.

        :param client: TON client to bind to the contract
        :param data: Contract data cell
        :param workchain: Target workchain (default: BASECHAIN)
        :return: New contract instance
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
        """
        Construct a contract wrapper from an existing on-chain address.

        Optionally fetches and caches the current contract state from the blockchain.
        If load_state is True and the request fails, sets state to default empty state.

        :param client: TON client to bind to the contract
        :param address: Address of the deployed contract (string or Address object)
        :param load_state: Whether to fetch current state from blockchain (default: True)
        :return: Contract instance bound to the specified address
        """
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
