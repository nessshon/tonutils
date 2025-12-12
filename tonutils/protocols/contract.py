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
    """Structural protocol for TON contract wrappers."""

    _data_model: t.Type[_D]
    """TlbScheme-compatible class representing decoded on-chain data."""

    VERSION: t.ClassVar[t.Union[ContractVersion, str]]
    """Logical contract version used as a key in CONTRACT_CODES."""

    @classmethod
    def get_default_code(cls) -> Cell:
        """
        Return default contract code for this contract class.

        Implementations usually resolve compiled code from a global registry
        (e.g. CONTRACT_CODES) by using cls.VERSION as a key.

        :return: Compiled contract code cell
        """

    @property
    def client(self) -> ClientProtocol:
        """TON client bound to this contract."""

    @property
    def address(self) -> Address:
        """Address of this contract."""

    @property
    def state_init(self) -> t.Optional[StateInit]:
        """Locally known StateInit for this contract, if any."""

    @property
    def state_info(self) -> ContractStateInfo:
        """
        Cached snapshot of the contract state.

        Implementations usually update this via refresh() or in constructors
        that read on-chain data.
        """

    @property
    def state_data(self) -> _D:
        """
        Decoded on-chain data in typed form.

        Implementations must decode the current data cell from state_info
        using the associated _data_model.
        """

    @property
    def balance(self) -> int:
        """
        Current contract balance in nanotons.

        :return: Balance from the latest known state
        """

    @property
    def state(self) -> ContractState:
        """
        Current lifecycle state of the contract.

        :return: One of ContractState values
        """

    @property
    def is_active(self) -> bool:
        """
        Check whether the contract is active.

        :return: True if state is ACTIVE
        """

    @property
    def is_frozen(self) -> bool:
        """
        Check whether the contract is frozen.

        :return: True if state is FROZEN
        """

    @property
    def is_uninit(self) -> bool:
        """
        Check whether the contract is uninitialized.

        :return: True if state is UNINIT
        """

    @property
    def is_nonexit(self) -> bool:
        """
        Check whether the contract does not exist on-chain.

        :return: True if state is NONEXIST
        """

    @property
    def last_transaction_lt(self) -> t.Optional[int]:
        """
        Logical time of the last known transaction for this contract.

        :return: Transaction LT or None if unknown
        """

    @property
    def last_transaction_hash(self) -> t.Optional[str]:
        """
        Hash of the last known transaction for this contract.

        :return: Transaction hash as hex string or None if unknown
        """

    @property
    def code(self) -> Cell:
        """
        Contract code cell from the latest known state.

        :return: Code cell
        """

    @property
    def data(self) -> Cell:
        """
        Contract data cell from the latest known state.

        :return: Data cell
        """

    async def refresh(self) -> None:
        """Refresh contract state from the blockchain."""

    @classmethod
    def from_state_init(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        state_init: StateInit,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract:
        """
        Construct a contract wrapper from a StateInit object.

        :param client: TON client to bind to the contract
        :param state_init: StateInit containing code and data
        :param workchain: Target workchain (default: BASECHAIN)
        :return: New contract instance
        """

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

        Implementations usually compose a StateInit from code and data and then
        delegate to from_state_init().

        :param client: TON client to bind to the contract
        :param code: Contract code cell
        :param data: Contract data cell
        :param workchain: Target workchain (default: BASECHAIN)
        :return: New contract instance
        """

    @classmethod
    def from_data(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        data: _D,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract:
        """
        Construct a contract wrapper from typed data.

        Composes StateInit by combining default code with the provided data,
        then delegates to from_state_init().

        :param client: TON client to bind to the contract
        :param data: Typed data object conforming to _data_model
        :param workchain: Target workchain (default: BASECHAIN)
        :return: New contract instance
        """

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

        :param client: TON client to bind to the contract
        :param address: Address of the deployed contract
        :param load_state: Whether to fetch current state from blockchain (default: True)
        :return: Contract instance bound to the specified address
        """
