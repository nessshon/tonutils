import base64
import typing as t

from nacl.public import PublicKey
from pydantic import field_validator, field_serializer

from tonutils.tonconnect.models._types import A, BaseModel


class IncomingMessage(BaseModel):
    """Encrypted message received from the TonConnect bridge.

    Attributes:
        from_wallet_public_key: Sender X25519 public key.
        message: Encrypted message bytes.
    """

    from_wallet_public_key: PublicKey = A("from")
    message: bytes

    @property
    def sender_public_key(self) -> PublicKey:
        """Sender X25519 public key."""
        return self.from_wallet_public_key

    @property
    def sender(self) -> str:
        """Hex-encoded sender public key."""
        return self.sender_public_key.encode().hex()

    @field_validator("from_wallet_public_key", mode="before")
    @classmethod
    def _v_from_wallet_public_key(cls, v: t.Any) -> PublicKey:
        if isinstance(v, PublicKey):
            return v
        return PublicKey(bytes.fromhex(v))

    @field_validator("message", mode="before")
    @classmethod
    def _v_message(cls, v: t.Any) -> bytes:
        if isinstance(v, bytes):
            return v
        return base64.b64decode(v, validate=True)

    @field_serializer("from_wallet_public_key")
    def _s_public_key(self, v: PublicKey) -> str:
        return v.encode().hex()

    @field_serializer("message")
    def _s_message(self, v: bytes) -> str:
        return base64.b64encode(v).decode("ascii")
