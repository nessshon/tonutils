from __future__ import annotations

import typing as t

from pytoniq_core import Address, Cell, StateInit

from tonutils.clients.protocol import ClientProtocol
from tonutils.types import AddressLike, ContractInfo, ContractState, WorkchainID

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
    """Logical contract version used as a key in `CONTRACT_CODES`."""

    @classmethod
    def get_default_code(cls) -> Cell:
        """Return default compiled code `Cell` for this contract version."""

    @property
    def client(self) -> ClientProtocol:
        """TON client bound to this contract."""

    @property
    def address(self) -> Address:
        """Address of this contract."""

    @property
    def state_init(self) -> t.Optional[StateInit]:
        """Locally known `StateInit`, or `None`."""

    @property
    def state_data(self) -> _D:
        """Decoded on-chain data in typed form."""

    @property
    def info(self) -> ContractInfo:
        """Cached on-chain state snapshot."""

    @property
    def balance(self) -> int:
        """Contract balance in nanotons."""

    @property
    def state(self) -> ContractState:
        """Current lifecycle state."""

    @property
    def is_active(self) -> bool:
        """`True` if state is `ACTIVE`."""

    @property
    def is_frozen(self) -> bool:
        """`True` if state is `FROZEN`."""

    @property
    def is_uninit(self) -> bool:
        """`True` if state is `UNINIT`."""

    @property
    def is_nonexit(self) -> bool:
        """`True` if state is `NONEXIST`."""

    @property
    def last_transaction_lt(self) -> t.Optional[int]:
        """Logical time of the last transaction, or `None`."""

    @property
    def last_transaction_hash(self) -> t.Optional[str]:
        """Hash of the last transaction as hex string, or `None`."""

    @property
    def code(self) -> Cell:
        """Contract code `Cell` from the latest known state."""

    @property
    def data(self) -> Cell:
        """Contract data `Cell` from the latest known state."""

    async def refresh(self) -> None:
        """Refresh contract state from the blockchain."""

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

    @classmethod
    def from_data(
        cls: t.Type[_TContract],
        client: ClientProtocol,
        data: _D,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> _TContract:
        """Construct from typed data.

        :param client: TON client.
        :param data: Typed data conforming to `_data_model`.
        :param workchain: Target workchain.
        :return: New contract instance.
        """

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
