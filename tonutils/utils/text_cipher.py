import base64
import binascii
import hashlib
import hmac
import os
import typing as t

from Cryptodome.Cipher import AES
from nacl.bindings import (
    crypto_sign_ed25519_sk_to_curve25519,
    crypto_sign_ed25519_pk_to_curve25519,
    crypto_scalarmult,
)
from pytoniq_core import Address, Cell

from ..exceptions import TextCipherError
from ..types.common import AddressLike
from ..types.keystructs import PublicKey, PrivateKey


class TextCipher:

    @staticmethod
    def _xor32(a: bytes, b: bytes) -> bytes:
        return bytes(x ^ y for x, y in zip(a, b))

    @staticmethod
    def _derive(shared: bytes, msg_key: bytes) -> tuple[bytes, bytes]:
        derived_bytes = hmac.new(shared, msg_key, hashlib.sha512).digest()
        return derived_bytes[:32], derived_bytes[32:48]

    @staticmethod
    def _msg_key(salt: bytes, data: bytes) -> bytes:
        return hmac.new(salt, data, hashlib.sha512).digest()[:16]

    @staticmethod
    def _make_plain(msg: bytes) -> bytes:
        p = 16 if len(msg) % 16 == 0 else 16 + (16 - (len(msg) % 16))
        return bytes([p]) + os.urandom(p - 1) + msg

    @staticmethod
    def _shared_key_from_ed25519(sk64: bytes, peer_pub32: bytes) -> bytes:
        sk_curve = crypto_sign_ed25519_sk_to_curve25519(sk64)
        pk_curve = crypto_sign_ed25519_pk_to_curve25519(peer_pub32)
        return crypto_scalarmult(sk_curve, pk_curve)

    @staticmethod
    def _parse_payload(payload: t.Union[Cell, bytes, str]) -> t.Tuple[bytes, ...]:
        from ..types import EncryptedTextComment

        if isinstance(payload, bytes):
            return payload[:32], payload[32:48], payload[48:]
        elif isinstance(payload, str):
            try:
                payload = bytes.fromhex(payload)
            except ValueError:
                pass
            try:
                payload = base64.b64decode(payload, validate=True)
            except (binascii.Error, ValueError):
                raise TextCipherError("Invalid payload encoding: not hex or base64")
            return payload[:32], payload[32:48], payload[48:]

        cell = EncryptedTextComment.deserialize(payload.begin_parse())
        return cell.pub_xor, cell.msg_key, cell.ciphertext

    @staticmethod
    def _salt(address: AddressLike) -> bytes:
        if isinstance(address, str):
            address = Address(address)
        salt = address.to_str(
            is_user_friendly=True,
            is_bounceable=True,
            is_test_only=False,
        )
        return salt.encode()

    @classmethod
    def encrypt(
        cls,
        payload: str,
        sender_address: AddressLike,
        our_private_key: PrivateKey,
        their_public_key: PublicKey,
    ) -> Cell:
        from ..types import EncryptedTextComment

        sk_ed25519_64 = our_private_key.keypair.bytes
        their_pubkey_32 = their_public_key.bytes
        our_pubkey_32 = our_private_key.public_key.bytes

        shared = cls._shared_key_from_ed25519(sk_ed25519_64, their_pubkey_32)
        padded_data = cls._make_plain(payload.encode("utf-8"))

        salt = cls._salt(sender_address)
        msg_key = cls._msg_key(salt, padded_data)

        key, iv = cls._derive(shared, msg_key)
        enc_data = AES.new(key, AES.MODE_CBC, iv).encrypt(padded_data)

        xor_key = cls._xor32(our_pubkey_32, their_pubkey_32)
        cell = EncryptedTextComment(xor_key, msg_key, enc_data)
        return cell.serialize()

    @classmethod
    def decrypt(
        cls,
        payload: t.Union[Cell, str, bytes],
        sender_address: AddressLike,
        our_public_key: PublicKey,
        our_private_key: PrivateKey,
    ) -> str:
        sk_ed25519_64 = our_private_key.keypair.bytes
        our_pubkey_32 = our_public_key.bytes

        pub_xor, msg_key, enc_data = cls._parse_payload(payload)
        their_pubkey_ed25519 = cls._xor32(pub_xor, our_pubkey_32)
        shared = cls._shared_key_from_ed25519(sk_ed25519_64, their_pubkey_ed25519)

        key, iv = cls._derive(shared, msg_key)
        dec_data = AES.new(key, AES.MODE_CBC, iv).decrypt(enc_data)

        salt = cls._salt(sender_address)
        if cls._msg_key(salt, dec_data) != msg_key:
            raise TextCipherError("Message key mismatch.")

        padding_size = dec_data[0]
        if not (16 <= padding_size <= 31):
            raise TextCipherError(
                f"Invalid padding length: got {padding_size} byte(s), "
                f"expected between 16 and 31 bytes."
            )
        if 1 + padding_size > len(dec_data):
            raise TextCipherError(
                f"Padding exceeds data length: "
                f"padding={padding_size}, total={len(dec_data)}."
            )

        comment = dec_data[padding_size:]
        return comment.decode()
