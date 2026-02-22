from __future__ import annotations

import typing as t

from nacl.public import Box, PrivateKey, PublicKey
from nacl.utils import random as random_bytes
from pydantic import field_validator, field_serializer

from tonutils.tonconnect.models._types import A, BaseModel


class SessionKeyPair(BaseModel):
    """X25519 key pair for TonConnect session encryption.

    Attributes:
        public_key: X25519 public key.
        secret_key: X25519 private key.
    """

    public_key: PublicKey = A("publicKey")
    secret_key: PrivateKey = A("secretKey")

    _NONCE_LENGTH: t.ClassVar[int] = 24

    @classmethod
    def generate(cls) -> SessionKeyPair:
        """Generate a new random key pair.

        :return: Fresh `SessionKeyPair`.
        """
        sk = PrivateKey.generate()
        return cls(public_key=sk.public_key, secret_key=sk)

    @property
    def session_id(self) -> str:
        """Hex-encoded public key used as the session identifier."""
        return self.public_key.encode().hex()

    def encrypt(self, message: bytes, receiver_public_key: PublicKey) -> bytes:
        """Encrypt a message for a receiver.

        :param message: Plaintext bytes.
        :param receiver_public_key: Receiver X25519 public key.
        :return: Nonce-prefixed ciphertext.
        """
        nonce = random_bytes(self._NONCE_LENGTH)
        box = Box(self.secret_key, receiver_public_key)
        ciphertext = box.encrypt(message, nonce).ciphertext
        return nonce + ciphertext

    def decrypt(self, message: bytes, sender_public_key: PublicKey) -> bytes:
        """Decrypt a message from a sender.

        :param message: Nonce-prefixed ciphertext.
        :param sender_public_key: Sender X25519 public key.
        :return: Decrypted plaintext bytes.
        """
        nonce = message[: self._NONCE_LENGTH]
        ciphertext = message[self._NONCE_LENGTH :]
        box = Box(self.secret_key, sender_public_key)
        return box.decrypt(ciphertext, nonce)

    @field_validator("public_key", mode="before")
    @classmethod
    def _v_public_key(cls, v: t.Any) -> PublicKey:
        if isinstance(v, PublicKey):
            return v
        return PublicKey(bytes.fromhex(v))

    @field_validator("secret_key", mode="before")
    @classmethod
    def _v_secret_key(cls, v: t.Any) -> PrivateKey:
        if isinstance(v, PrivateKey):
            return v
        return PrivateKey(bytes.fromhex(v))

    @field_serializer("public_key")
    def _s_public_key(self, v: PublicKey) -> str:
        return v.encode().hex()

    @field_serializer("secret_key")
    def _s_secret_key(self, v: PrivateKey) -> str:
        return v.encode().hex()


class BridgeProviderSession(BaseModel):
    """Active bridge session with wallet encryption keys.

    Attributes:
        session_keypair: Session X25519 key pair.
        wallet_public_key: Wallet X25519 public key.
        bridge_url: Bridge base URL.
    """

    session_keypair: SessionKeyPair = A("sessionKeyPair")
    wallet_public_key: PublicKey = A("walletPublicKey")
    bridge_url: str = A("bridgeUrl")

    @property
    def receiver_public_key(self) -> PublicKey:
        """Wallet X25519 public key."""
        return self.wallet_public_key

    @property
    def receiver(self) -> str:
        """Hex-encoded wallet public key."""
        return self.receiver_public_key.encode().hex()

    @field_validator("wallet_public_key", mode="before")
    @classmethod
    def _v_wallet_public_key(cls, v: t.Any) -> PublicKey:
        if isinstance(v, PublicKey):
            return v
        return PublicKey(bytes.fromhex(v))

    @field_serializer("wallet_public_key")
    def _s_wallet_public_key(self, v: PublicKey) -> str:
        return v.encode().hex()
