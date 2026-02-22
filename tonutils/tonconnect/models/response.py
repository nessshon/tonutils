import typing as t

from pydantic import Field, RootModel
from pytoniq_core import Cell, MessageAny

from tonutils.tonconnect.models._types import (
    A,
    BaseModel,
    ChainId,
    TonAddress,
    TonPublicKey,
    WalletStateInit,
    Binary64,
)
from tonutils.tonconnect.models.device import Device
from tonutils.tonconnect.models.payload import SignDataPayload
from tonutils.tonconnect.models.proof import TonProofData
from tonutils.utils import normalize_hash


class EventBase(BaseModel):
    """Base for wallet events with a monotonic ID.

    Attributes:
        id: Monotonic event identifier.
    """

    id: int


class TonAddressItemReply(BaseModel):
    """Wallet reply containing TON address and keys.

    Attributes:
        name: Item type literal.
        address: Wallet address.
        network: Network identifier.
        state_init: Wallet `StateInit`.
        public_key: Wallet public key.
    """

    name: t.Literal["ton_addr"]
    address: TonAddress
    network: ChainId
    state_init: WalletStateInit = A("walletStateInit")
    public_key: TonPublicKey = A("publicKey")


class TonProofItemReply(BaseModel):
    """Wallet reply containing TON Proof data.

    Attributes:
        name: Item type literal.
        proof: Proof data, or `None`.
    """

    name: t.Literal["ton_proof"]
    proof: t.Optional[TonProofData] = None


ConnectEventItemReply: t.TypeAlias = t.Annotated[
    t.Union[TonAddressItemReply, TonProofItemReply],
    Field(discriminator="name"),  # type: ignore
]


class ConnectEventPayload(BaseModel):
    """Payload of a successful connect event.

    Attributes:
        items: Connect reply items.
        device: Wallet device information.
    """

    items: t.List[ConnectEventItemReply]
    device: Device


class DisconnectEventPayload(BaseModel):
    """Payload of a successful disconnect event.

    Attributes:
        data: Additional data (typically empty).
    """

    data: dict = Field(default_factory=dict)


class EventErrorPayload(BaseModel):
    """Payload of an event error.

    Attributes:
        code: Error code.
        message: Error message.
    """

    code: int
    message: str


class ConnectEventSuccess(EventBase):
    """Successful wallet connect event.

    Attributes:
        event: Event type literal.
        payload: Connect event payload.
    """

    event: t.Literal["connect"]
    payload: ConnectEventPayload


class ConnectEventError(EventBase):
    """Failed wallet connect event.

    Attributes:
        event: Event type literal.
        payload: Error payload.
    """

    event: t.Literal["connect_error"]
    payload: EventErrorPayload


class DisconnectEventSuccess(EventBase):
    """Successful wallet disconnect event.

    Attributes:
        event: Event type literal.
        payload: Additional data (typically empty).
    """

    event: t.Literal["disconnect"]
    payload: dict = Field(default_factory=dict)


class DisconnectEventError(EventBase):
    """Failed wallet disconnect event.

    Attributes:
        event: Event type literal.
        payload: Error payload.
    """

    event: t.Literal["disconnect_error"]
    payload: EventErrorPayload


ConnectEvent: t.TypeAlias = t.Union[
    ConnectEventSuccess,
    ConnectEventError,
]

DisconnectEvent: t.TypeAlias = t.Union[
    DisconnectEventSuccess,
    DisconnectEventError,
]

WalletEvent: t.TypeAlias = t.Union[
    ConnectEvent,
    DisconnectEvent,
]


class RpcBase(BaseModel):
    """Base for wallet RPC responses.

    Attributes:
        id: Request identifier string.
    """

    id: str


class RpcRequestErrorPayload(BaseModel):
    """Error payload in an RPC response.

    Attributes:
        code: Error code.
        message: Error message.
        data: Additional error data, or `None`.
    """

    code: int
    message: str
    data: t.Optional[t.Any] = None


class WalletResponseError(RpcBase):
    """Wallet RPC error response.

    Attributes:
        error: Error payload.
    """

    error: RpcRequestErrorPayload


class SendTransactionResult(RootModel[str]):
    """Result of a `sendTransaction` RPC call."""

    @property
    def boc(self) -> str:
        """Base64-encoded BOC string."""
        return self.root

    def to_cell(self) -> Cell:
        """Deserialize the BOC to a `Cell`.

        :return: Parsed `Cell`.
        """
        return Cell.one_from_boc(self.root)

    @property
    def normalized_hash(self) -> str:
        """Normalized message hash for tracking."""
        msg = MessageAny.deserialize(self.to_cell().begin_parse())
        return normalize_hash(msg)


class RpcResponseSuccessBase(RpcBase):
    """Base for successful RPC responses."""

    pass


class SignDataResult(BaseModel):
    """Result of a `signData` RPC call.

    Attributes:
        signature: Ed25519 signature (64 bytes).
        address: Signer wallet address.
        timestamp: Signing unix timestamp.
        domain: dApp domain.
        payload: Signed data payload.
    """

    signature: Binary64
    address: TonAddress
    timestamp: int
    domain: str
    payload: SignDataPayload


class SendTransactionRpcResponseSuccess(RpcResponseSuccessBase):
    """Successful `sendTransaction` RPC response.

    Attributes:
        result: Transaction result.
    """

    result: SendTransactionResult


class DisconnectRpcResponseSuccess(RpcResponseSuccessBase):
    """Successful `disconnect` RPC response.

    Attributes:
        result: Additional data (typically empty).
    """

    result: dict = Field(default_factory=dict)


class SignDataRpcResponseSuccess(RpcResponseSuccessBase):
    """Successful `signData` RPC response.

    Attributes:
        result: Sign data result.
    """

    result: SignDataResult


WalletResponseSuccess: t.TypeAlias = t.Union[
    DisconnectRpcResponseSuccess,
    SendTransactionRpcResponseSuccess,
    SignDataRpcResponseSuccess,
]

WalletResponse: t.TypeAlias = t.Union[
    WalletResponseSuccess,
    WalletResponseError,
]

WalletMessage: t.TypeAlias = t.Union[
    WalletEvent,
    WalletResponse,
]
