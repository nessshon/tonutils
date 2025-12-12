from __future__ import annotations

import asyncio
import hashlib
import secrets
import typing as t
from contextlib import suppress

from nacl.bindings import crypto_scalarmult
from pytoniq_core.crypto.ciphers import (
    Client,
    Server,
    aes_ctr_decrypt,
    aes_ctr_encrypt,
    create_aes_ctr_cipher,
)

from tonutils.clients.adnl.provider.models import LiteServer
from tonutils.exceptions import (
    AdnlHandshakeError,
    AdnlTransportCipherError,
    AdnlTransportFrameError,
    AdnlTransportStateError,
    AdnlTransportError,
)


class AdnlTcpTransport:
    """
    ADNL TCP transport for encrypted communication with TON liteservers.

    Implements the ADNL protocol over TCP, providing:
    - Elliptic curve Diffie-Hellman (ECDH) key exchange
    - AES-CTR encryption for all traffic after handshake
    - Frame-based message protocol with checksums
    - Automatic connection management and error handling

    The transport performs a cryptographic handshake on connect, establishes
    bidirectional encrypted channels, and maintains a background reader task
    for incoming frames.
    """

    def __init__(self, node: LiteServer, timeout: int) -> None:
        """
        Initialize ADNL TCP transport for a liteserver connection.

        :param node: Liteserver configuration with host, port, and public key
        :param timeout: Timeout in seconds for connection and I/O operations
        """
        self.server = Server(
            host=node.host,
            port=node.port,
            pub_key=node.pub_key,
        )
        self.client = Client(Client.generate_ed25519_private_key())

        self.timeout = timeout
        self.enc_cipher = None
        self.dec_cipher = None

        self.loop: t.Optional[asyncio.AbstractEventLoop] = None
        self.reader: t.Optional[asyncio.StreamReader] = None
        self.writer: t.Optional[asyncio.StreamWriter] = None

        self._incoming: asyncio.Queue[bytes] = asyncio.Queue()
        self._reader_task: t.Optional[asyncio.Task] = None

        self._connected = False
        self._closing = False

    @property
    def is_connected(self) -> bool:
        """Check if the transport is currently connected."""
        return self._connected

    @staticmethod
    def _build_frame(data: bytes) -> bytes:
        """
        Build an ADNL frame with length prefix, nonce, payload, and checksum.

        Frame structure:
        - 4 bytes: total length (payload + 64 bytes overhead) in little-endian
        - 32 bytes: random nonce
        - N bytes: payload data
        - 32 bytes: SHA-256 checksum of (nonce + payload)

        :param data: Payload bytes to frame
        """
        result = (len(data) + 64).to_bytes(4, "little")
        result += secrets.token_bytes(32)
        result += data
        result += hashlib.sha256(result[4:]).digest()
        return result

    def _build_handshake(self) -> bytes:
        """
        Build ADNL handshake packet with ECDH key exchange.

        Generates ephemeral AES-CTR keys, performs Curve25519 key exchange with
        the server's public key, and encrypts the session parameters.

        Handshake structure:
        - 32 bytes: server key ID (SHA-256 of server public key)
        - 32 bytes: client Ed25519 public key
        - 32 bytes: checksum of encrypted data
        - 160 bytes: encrypted session parameters (AES keys + nonces)
        """
        rand = secrets.token_bytes(160)

        self.dec_cipher = create_aes_ctr_cipher(rand[0:32], rand[64:80])
        self.enc_cipher = create_aes_ctr_cipher(rand[32:64], rand[80:96])

        checksum = hashlib.sha256(rand).digest()
        shared_key = crypto_scalarmult(
            self.client.x25519_private.encode(),
            self.server.x25519_public.encode(),
        )
        init_cipher = create_aes_ctr_cipher(
            shared_key[0:16] + checksum[16:32],
            checksum[0:4] + shared_key[20:32],
        )
        data = aes_ctr_encrypt(init_cipher, rand)

        return (
            self.server.get_key_id()
            + self.client.ed25519_public.encode()
            + checksum
            + data
        )

    async def _flush(self) -> None:
        """Flush the TCP write buffer."""
        if self.writer is None:
            raise AdnlTransportStateError("`writer` is not initialized")
        try:
            await self.writer.drain()
        except ConnectionError:
            await self.close()
            raise

    def encrypt_frame(self, data: bytes) -> bytes:
        """
        Encrypt a frame using the session's encryption cipher.

        :param data: Plaintext frame bytes
        """
        if self.enc_cipher is None:
            raise AdnlTransportCipherError("`encryption`")
        return aes_ctr_encrypt(self.enc_cipher, data)

    def decrypt_frame(self, data: bytes) -> bytes:
        """
        Decrypt a frame using the session's decryption cipher.

        :param data: Encrypted frame bytes
        """
        if self.dec_cipher is None:
            raise AdnlTransportCipherError("`decryption`")
        return aes_ctr_decrypt(self.dec_cipher, data)

    async def connect(self) -> None:
        """Establish encrypted connection to the liteserver."""
        if self._connected:
            raise AdnlTransportStateError("already connected")

        self.loop = asyncio.get_running_loop()

        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.server.host, self.server.port),
            timeout=self.timeout,
        )
        if self.writer is None or self.reader is None:
            raise AdnlTransportError("failed to initialize TCP streams")

        try:
            handshake = self._build_handshake()
            self.writer.write(handshake)
            await self._flush()

            try:
                await asyncio.wait_for(
                    self.read_frame(discard=True),
                    timeout=self.timeout,
                )
            except asyncio.IncompleteReadError as exc:
                raise AdnlHandshakeError(
                    "ADNL handshake failed: remote closed connection"
                ) from exc
            except asyncio.TimeoutError as exc:
                raise AdnlHandshakeError(
                    f"Timed out waiting for initial ADNL handshake ({self.timeout}s)"
                ) from exc
            self._connected = True
            self._reader_task = asyncio.create_task(
                self.frame_reader_loop(),
                name="frame_reader_loop",
            )
        except Exception:
            await self.close()
            raise

    async def send_adnl_packet(self, payload: bytes) -> None:
        """
        Send an ADNL packet to the liteserver.

        Frames, encrypts, and transmits the payload.

        :param payload: Raw ADNL packet bytes
        """
        if not self._connected or self.writer is None:
            raise AdnlTransportStateError("transport is not connected")

        packet = self._build_frame(payload)
        encrypted = self.encrypt_frame(packet)

        self.writer.write(encrypted)
        await self._flush()

    async def recv_adnl_packet(self) -> bytes:
        """
        Receive an ADNL packet from the liteserver.

        Blocks until a complete packet is available from the background reader.
        """
        if not self._connected:
            raise AdnlTransportStateError("transport is not connected")
        return await self._incoming.get()

    async def read_frame(self, discard: bool = False) -> t.Optional[bytes]:
        """
        Read and validate a single ADNL frame from the stream.

        Frame validation:
        - Reads 4-byte length prefix
        - Reads and decrypts frame body
        - Verifies SHA-256 checksum

        :param discard: If True, validates but returns None (used for handshake ack)
        """
        if self.reader is None:
            raise AdnlTransportStateError("`reader` is not initialized")

        length_enc = await self.reader.readexactly(4)
        length_dec = self.decrypt_frame(length_enc)
        data_len = int.from_bytes(length_dec, "little")

        if data_len <= 0:
            raise AdnlTransportFrameError(f"non-positive length `{data_len}`")

        data_enc = await self.reader.readexactly(data_len)
        data = self.decrypt_frame(data_enc)

        if len(data) < 32:
            raise AdnlTransportFrameError("frame is too short")

        payload, checksum = data[:-32], data[-32:]
        if hashlib.sha256(payload).digest() != checksum:
            raise AdnlTransportFrameError("checksum mismatch")

        if discard:
            return None
        return payload

    async def frame_reader_loop(self) -> None:
        """Background task that continuously reads frames and queues them."""
        try:
            while True:
                frame = await self.read_frame(discard=False)
                if frame is None:
                    continue
                await self._incoming.put(frame)
        except asyncio.CancelledError:
            pass
        except (
            asyncio.IncompleteReadError,
            ConnectionAbortedError,
            ConnectionError,
            TimeoutError,
            OSError,
        ):
            pass
        finally:
            self._connected = False
            if not self._closing:
                asyncio.create_task(self.close())

    async def close(self) -> None:
        """Close the transport and clean up all resources."""
        if self._closing:
            return
        self._closing = True
        try:
            self._connected = False

            task, self._reader_task = self._reader_task, None
            if task is not None and not task.done():
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

            writer, self.writer = self.writer, None
            self.reader = None

            if writer is not None:
                try:
                    writer.close()
                finally:
                    with suppress(Exception):
                        await writer.wait_closed()

            while not self._incoming.empty():
                try:
                    self._incoming.get_nowait()
                    self._incoming.task_done()
                except asyncio.QueueEmpty:
                    break

            self.enc_cipher = None
            self.dec_cipher = None
        finally:
            self._closing = False
