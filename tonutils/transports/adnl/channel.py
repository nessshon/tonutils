import hashlib
import typing as t

from ton_core import (
    Client,
    Server,
    aes_ctr_decrypt,
    aes_ctr_encrypt,
    create_aes_ctr_cipher,
    get_shared_key,
)

_PUB_AES_PREFIX = b"\xd4\xad\xbc\x2d"
"""TL constructor prefix for ``pub.aes`` (0x2dbcadd4 LE)."""


def _aes_key_id(key: bytes) -> bytes:
    """Compute ``pub.aes`` key ID.

    :param key: Raw key material (32 bytes).
    :return: 32-byte SHA-256 hash.
    """
    return hashlib.sha256(_PUB_AES_PREFIX + key).digest()


def _aes_cipher(key: bytes, checksum: bytes) -> t.Any:
    """Create per-message AES-CTR cipher from key and data hash.

    :param key: Shared key (enc or dec).
    :param checksum: SHA-256 of the plaintext.
    :return: AES-CTR cipher object.
    """
    return create_aes_ctr_cipher(
        key[0:16] + checksum[16:32],
        checksum[0:4] + key[20:32],
    )


class AdnlChannel:
    """Per-peer ADNL channel with shared-secret encryption.

    Direction is determined by comparing local key ID to peer key ID.
    Each encrypt/decrypt operation creates a fresh AES-CTR cipher
    using the shared key and the SHA-256 of the plaintext.
    """

    def __init__(
        self,
        client: Client,
        server: Server,
        local_id: bytes,
        peer_id: bytes,
    ) -> None:
        """Initialize the ADNL channel.

        :param client: Channel ``Client`` (our key pair).
        :param server: Channel ``Server`` (peer public key).
        :param local_id: Our ADNL key ID (32 bytes).
        :param peer_id: Peer ADNL key ID (32 bytes).
        """
        self._client = client
        self._server = server

        shared = get_shared_key(
            client.x25519_private.encode(),
            server.x25519_public.encode(),
        )

        if local_id > peer_id:
            self._enc_key = shared
            self._dec_key = shared[::-1]
        elif local_id < peer_id:
            self._enc_key = shared[::-1]
            self._dec_key = shared
        else:
            self._enc_key = shared
            self._dec_key = shared

        self._send_id = _aes_key_id(self._enc_key)
        self._recv_id = _aes_key_id(self._dec_key)

    @property
    def send_id(self) -> bytes:
        """32-byte key ID prepended to outgoing channel packets."""
        return self._send_id

    @property
    def recv_id(self) -> bytes:
        """32-byte key ID expected on incoming channel packets."""
        return self._recv_id

    @property
    def client(self) -> Client:
        """Our channel key pair."""
        return self._client

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data and build a channel packet.

        :param data: Plaintext bytes.
        :return: ``send_id(32) + checksum(32) + encrypted`` bytes.
        """
        checksum = hashlib.sha256(data).digest()
        cipher = _aes_cipher(self._enc_key, checksum)
        encrypted = aes_ctr_encrypt(cipher, data)
        return self._send_id + checksum + encrypted

    def decrypt(self, encrypted: bytes, checksum: bytes) -> bytes:
        """Decrypt channel packet payload and verify integrity.

        :param encrypted: Ciphertext bytes (after key_id + checksum).
        :param checksum: SHA-256 checksum from the packet header.
        :return: Decrypted plaintext bytes.
        :raises ValueError: If checksum does not match decrypted data.
        """
        cipher = _aes_cipher(self._dec_key, checksum)
        plaintext = aes_ctr_decrypt(cipher, encrypted)
        if hashlib.sha256(plaintext).digest() != checksum:
            raise ValueError("channel packet checksum mismatch")
        return plaintext
