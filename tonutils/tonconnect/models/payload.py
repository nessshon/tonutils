import base64
import time
import typing as t

from pydantic import Field, field_validator, field_serializer
from pytoniq_core import Cell

from tonutils.contracts import TextCommentBody
from tonutils.tonconnect.models._types import (
    A,
    BaseModel,
    BocCell,
    OptionalBocCell,
    OptionalChainId,
    OptionalTonAddress,
    OptionalWalletStateInit,
    TonAddress,
)


class SendTransactionMessage(BaseModel):
    """Single outgoing message within a `sendTransaction` request.

    Attributes:
        address: Destination address.
        amount: Transfer amount in nanotons.
        state_init: Contract `StateInit`, or `None`.
        payload: Message body `Cell`, or `None`.
        extra_currency: Extra currency map, or `None`.
    """

    address: TonAddress
    amount: int
    state_init: OptionalWalletStateInit = A("stateInit", default=None)
    payload: t.Union[OptionalBocCell, t.Optional[str]] = None
    extra_currency: t.Optional[t.Dict[int, str]] = A("extraCurrency", default=None)

    @field_validator("amount", mode="before")
    @classmethod
    def _v_amount(cls, v: t.Any) -> int:
        if isinstance(v, int):
            return v
        return int(v)

    @field_serializer("amount")
    def _s_amount(self, v: int) -> str:
        return str(v)

    @field_validator("payload", mode="before")
    @classmethod
    def _v_payload(cls, v: t.Any) -> t.Optional[Cell]:
        if isinstance(v, str):
            return TextCommentBody(v).serialize()
        return v


class SendTransactionPayload(BaseModel):
    """Payload for a `sendTransaction` RPC request.

    Attributes:
        network: Target network, or `None`.
        from_address: Sender address override, or `None`.
        valid_until: Expiry unix timestamp.
        messages: Outgoing messages.
    """

    network: OptionalChainId = None
    from_address: OptionalTonAddress = A("from", default=None)
    valid_until: int = A("validUntil", default=None)
    messages: t.List[SendTransactionMessage] = Field(default_factory=list)

    @field_validator("valid_until", mode="before")
    @classmethod
    def _v_valid_until(cls, v: t.Any) -> int:
        if v is None:
            return int(time.time()) + 5 * 60
        return v


class BaseSignDataPayload(BaseModel):
    """Common fields for all `signData` payload types.

    Attributes:
        network: Target network, or `None`.
        from_address: Wallet address, or `None`.
    """

    network: OptionalChainId = None
    from_address: OptionalTonAddress = A("from", default=None)


class SignDataPayloadText(BaseSignDataPayload):
    """Text payload for `signData`.

    Attributes:
        type: Payload type literal.
        text: UTF-8 text to sign.
    """

    type: t.Literal["text"] = "text"
    text: str


class SignDataPayloadBinary(BaseSignDataPayload):
    """Binary payload for `signData`.

    Attributes:
        type: Payload type literal.
        raw_bytes: Raw bytes to sign.
    """

    type: t.Literal["binary"] = "binary"
    raw_bytes: bytes = A("bytes")

    @field_validator("raw_bytes", mode="before")
    @classmethod
    def _v_raw_bytes(cls, v: t.Any) -> bytes:
        if isinstance(v, bytes):
            return v
        s = str(v).strip()
        padded = s + "=" * (-len(s) % 4)
        return base64.b64decode(padded, validate=True)

    @field_serializer("raw_bytes")
    def _s_raw_bytes(self, v: bytes) -> str:
        return base64.b64encode(v).decode("ascii")


class SignDataPayloadCell(BaseSignDataPayload):
    """Cell payload for `signData`.

    Attributes:
        type: Payload type literal.
        tlb_schema: TL-B schema string.
        cell: Signing payload `Cell`.
    """

    type: t.Literal["cell"] = "cell"
    tlb_schema: str = A("schema")
    cell: BocCell


SignDataPayload: t.TypeAlias = t.Annotated[
    t.Union[
        SignDataPayloadBinary,
        SignDataPayloadCell,
        SignDataPayloadText,
    ],
    Field(discriminator="type"),  # type: ignore
]
