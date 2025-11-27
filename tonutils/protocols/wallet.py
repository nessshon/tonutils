from __future__ import annotations

import typing as t

from pytoniq_core import Cell, StateInit, WalletMessage

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import (
    AddressLike,
    PublicKey,
    PrivateKey,
    SendMode,
    WorkchainID,
    DEFAULT_SENDMODE,
)

if t.TYPE_CHECKING:
    from tonutils.contracts.wallet.messages import (
        ExternalMessage,
        BaseMessageBuilder,
    )

_D = t.TypeVar("_D")
_C = t.TypeVar("_C")
_P = t.TypeVar("_P")

_TWallet = t.TypeVar("_TWallet")


@t.runtime_checkable
class WalletProtocol(ContractProtocol, t.Protocol[_D, _C, _P]):
    _data_model: t.Type[_D]
    _config_model: t.Type[_C]
    _params_model: t.Type[_P]

    MAX_MESSAGES: t.ClassVar[int]

    @property
    def config(self) -> _C: ...

    @property
    def state_data(self) -> _D: ...

    @property
    def public_key(self) -> t.Optional[PublicKey]: ...

    @property
    def private_key(self) -> t.Optional[PrivateKey]: ...

    @classmethod
    def from_private_key(
        cls: t.Type[_TWallet],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[_C] = None,
    ) -> _TWallet: ...

    @classmethod
    def from_mnemonic(
        cls: t.Type[_TWallet],
        client: ClientProtocol,
        mnemonic: t.Union[t.List[str], str],
        validate: bool = True,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[t.Any] = None,
    ) -> t.Tuple[_TWallet, PublicKey, PrivateKey, t.List[str]]: ...

    @classmethod
    def create(
        cls: t.Type[_TWallet],
        client: ClientProtocol,
        mnemonic_length: int = 24,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[t.Any] = None,
    ) -> t.Tuple[_TWallet, PublicKey, PrivateKey, t.List[str]]: ...

    async def build_external_message(
        self,
        messages: t.List[t.Union[WalletMessage, BaseMessageBuilder]],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage: ...

    async def batch_transfer_message(
        self: _TWallet,
        messages: t.List[t.Union[WalletMessage, BaseMessageBuilder]],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage: ...

    async def transfer_message(
        self: _TWallet,
        message: t.Union[WalletMessage, BaseMessageBuilder],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage: ...

    async def transfer(
        self: _TWallet,
        destination: AddressLike,
        amount: int,
        body: t.Optional[t.Union[Cell, str]] = None,
        state_init: t.Optional[StateInit] = None,
        send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE,
        bounce: t.Optional[bool] = None,
        params: t.Optional[_P] = None,
    ) -> ExternalMessage: ...
