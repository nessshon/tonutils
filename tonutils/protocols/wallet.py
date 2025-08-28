from __future__ import annotations

import typing as t

from pytoniq_core import (
    Cell,
    StateInit,
    WalletMessage,
)

from .client import ClientProtocol
from .contract import ContractProtocol
from ..types import (
    AddressLike,
    SendMode,
    PrivateKey,
    PublicKey,
    WorkchainID,
    TransferMessage,
    TransferNFTMessage,
    TransferJettonMessage,
)

D = t.TypeVar("D")
C = t.TypeVar("C")
P = t.TypeVar("P")

TWallet = t.TypeVar("TWallet")


@t.runtime_checkable
class WalletProtocol(ContractProtocol, t.Protocol[D, C, P]):
    _data_model: t.Type[D]
    _config_model: t.Type[C]
    _params_model: t.Type[P]

    MAX_MESSAGES: t.ClassVar[int]

    @property
    def config(self) -> C: ...

    @property
    def state_data(self) -> D: ...

    @property
    def public_key(self) -> t.Optional[PublicKey]: ...

    @property
    def private_key(self) -> t.Optional[PrivateKey]: ...

    @classmethod
    def from_private_key(
        cls: t.Type[TWallet],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[C] = None,
    ) -> TWallet: ...

    @classmethod
    def from_mnemonic(
        cls: t.Type[TWallet],
        client: ClientProtocol,
        mnemonic: t.Union[t.List[str], str],
        validate: bool = True,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[t.Any] = None,
    ) -> t.Tuple[TWallet, PublicKey, PrivateKey, t.List[str]]: ...

    @classmethod
    def create(
        cls: t.Type[TWallet],
        client: ClientProtocol,
        mnemonic_length: int = 24,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[t.Any] = None,
    ) -> t.Tuple[TWallet, PublicKey, PrivateKey, t.List[str]]: ...

    async def raw_transfer(
        self: TWallet,
        messages: t.List[WalletMessage],
        params: t.Optional[P] = None,
    ) -> str: ...

    async def transfer(
        self: TWallet,
        destination: AddressLike,
        value: int,
        body: t.Optional[t.Union[Cell, str]] = None,
        state_init: t.Optional[StateInit] = None,
        send_mode: t.Optional[t.Union[SendMode, int]] = None,
        bounce: t.Optional[bool] = None,
        params: t.Optional[P] = None,
    ) -> str: ...

    async def transfer_message(
        self: TWallet,
        message: t.Union[
            TransferMessage,
            TransferNFTMessage,
            TransferJettonMessage,
        ],
        params: t.Optional[P] = None,
    ) -> str: ...

    async def batch_transfer_message(
        self: TWallet,
        messages: t.List[
            t.Union[
                TransferMessage,
                TransferNFTMessage,
                TransferJettonMessage,
            ]
        ],
        params: t.Optional[P] = None,
    ) -> str: ...
