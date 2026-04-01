from __future__ import annotations

import asyncio
import hashlib
import time
import typing as t
from dataclasses import dataclass

from ton_core import (
    Client,
    Server,
    TlGenerator,
    aes_ctr_decrypt,
    aes_ctr_encrypt,
    create_aes_ctr_cipher,
    get_random,
    get_shared_key,
)

from tonutils.exceptions import NotConnectedError, ProviderTimeoutError, TransportError

if t.TYPE_CHECKING:
    from tonutils.transports.adnl.channel import AdnlChannel

_PUB_ED25519_PREFIX = b"\xc6\xb4\x13\x48"
"""TL constructor prefix for ``pub.ed25519`` (0x4813b4c6 LE)."""


def _compute_key_id(pub_key: bytes) -> bytes:
    """Compute ADNL key ID from Ed25519 public key.

    :param pub_key: Ed25519 public key (32 bytes).
    :return: 32-byte SHA-256 key ID.
    """
    return hashlib.sha256(_PUB_ED25519_PREFIX + pub_key).digest()


@dataclass
class _PeerState:
    """Per-peer state for ADNL-UDP connections."""

    host: str
    """Remote IP address."""

    port: int
    """Remote UDP port."""

    pub_key: bytes
    """Ed25519 public key (32 bytes)."""

    peer_id: bytes
    """ADNL key ID (32 bytes)."""

    endpoint: str = ""
    """``host:port`` string."""

    channel: AdnlChannel | None = None
    """Established ADNL channel, or ``None``."""

    seqno: int = 0
    """Outgoing sequence number."""

    confirm_seqno: int = 0
    """Last confirmed incoming sequence number."""

    reinit_date: int = 0
    """Local reinitialization timestamp."""

    dst_reinit_date: int = 0
    """Remote reinitialization timestamp."""

    def __post_init__(self) -> None:
        """Set default ``endpoint`` from ``host`` and ``port`` if empty."""
        if not self.endpoint:
            self.endpoint = f"{self.host}:{self.port}"


class _UdpProtocol(asyncio.DatagramProtocol):
    """Asyncio DatagramProtocol adapter that queues incoming datagrams."""

    def __init__(self, incoming: asyncio.Queue[tuple[bytes, tuple[str, int]]]) -> None:
        """Initialize the UDP protocol adapter.

        :param incoming: Queue for received datagrams.
        """
        self._incoming = incoming
        self.transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Handle connection establishment.

        :param transport: The datagram transport created by the event loop.
        """
        self.transport = t.cast("asyncio.DatagramTransport", transport)

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle incoming datagram.

        :param data: Raw datagram bytes.
        :param addr: Sender ``(host, port)`` tuple.
        """
        self._incoming.put_nowait((data, addr))

    def error_received(self, exc: Exception | None) -> None:
        """Handle protocol error.

        :param exc: Exception that occurred, or ``None``.
        """

    def connection_lost(self, exc: Exception | None) -> None:
        """Handle connection loss.

        :param exc: Exception that caused the loss, or ``None`` for clean close.
        """


class AdnlUdpTransport:
    """ADNL UDP transport for DHT node communication.

    Manages a single UDP socket with per-peer channel-based encryption.
    Uses Ed25519 for packet signing and Curve25519 ECDH for key exchange.
    """

    def __init__(self) -> None:
        """Initialize the ADNL UDP transport with a fresh Ed25519 key pair."""
        self._client = Client(Client.generate_ed25519_private_key())
        self._local_pub = bytes(self._client.ed25519_public)
        self._local_key_id = _compute_key_id(self._local_pub)

        self.tl_schemas = TlGenerator.with_default_schemas().generate()
        self._pkt_schema = self.tl_schemas.get_by_name("adnl.packetContents")

        self._incoming: asyncio.Queue[tuple[bytes, tuple[str, int]]] = asyncio.Queue()
        self._protocol: _UdpProtocol | None = None
        self._udp_transport: asyncio.DatagramTransport | None = None

        self._peers: dict[str, _PeerState] = {}
        self._channels: dict[bytes, _PeerState] = {}
        self._channel_pending: dict[str, asyncio.Future[t.Any]] = {}

        self._bound = False

    @property
    def local_key_id(self) -> bytes:
        """SHA-256 key ID of the local public key."""
        return self._local_key_id

    @property
    def bound(self) -> bool:
        """``True`` if the UDP socket is bound."""
        return self._bound

    @staticmethod
    def _get_rand() -> bytes:
        """Generate random padding for ADNL packets.

        :return: 7- or 15-byte random padding.
        """
        rand = get_random(16)
        if rand[0] & 1 > 0:
            return rand[1:]
        return rand[1:8]

    async def bind(self, host: str = "0.0.0.0", port: int = 0) -> None:
        """Bind the UDP socket.

        :param host: Local bind address.
        :param port: Local bind port (0 for ephemeral).
        """
        if self._bound:
            return

        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: _UdpProtocol(self._incoming),
            local_addr=(host, port),
        )
        self._udp_transport = transport
        self._protocol = protocol
        self._bound = True

    def get_or_create_peer_raw(
        self,
        *,
        host: str,
        port: int,
        pub_key: bytes,
    ) -> _PeerState:
        """Get existing peer or create new state from raw parameters.

        :param host: IP address in dotted-decimal notation.
        :param port: UDP port number.
        :param pub_key: Ed25519 public key (32 bytes).
        :return: Peer state.
        """
        key = f"{host}:{port}"
        if key in self._peers:
            return self._peers[key]

        peer_id = _compute_key_id(pub_key)
        peer = _PeerState(
            host=host,
            port=port,
            pub_key=pub_key,
            peer_id=peer_id,
        )
        self._peers[key] = peer
        return peer

    @staticmethod
    def _compute_flags(data: dict[str, t.Any]) -> dict[str, t.Any]:
        """Compute the ``flags`` bitfield from present keys.

        :param data: Packet contents dict.
        :return: Data with ``flags`` set.
        """
        flags = 0
        if "from" in data:
            flags |= 1 << 0
        if "from_short" in data:
            flags |= 1 << 1
        if "message" in data:
            flags |= 1 << 2
        if "messages" in data:
            flags |= 1 << 3
        if "address" in data:
            flags |= 1 << 4
        if "priority_address" in data:
            flags |= 1 << 5
        if "seqno" in data:
            flags |= 1 << 6
        if "confirm_seqno" in data:
            flags |= 1 << 7
        if "recv_addr_list_version" in data:
            flags |= 1 << 8
        if "recv_priority_addr_list_version" in data:
            flags |= 1 << 9
        if "reinit_date" in data or "dst_reinit_date" in data:
            flags |= 1 << 10
        if "signature" in data:
            flags |= 1 << 11
        data["flags"] = flags
        return data

    def _serialize_packet(self, data: dict[str, t.Any]) -> bytes:
        """Serialize ``adnl.packetContents`` with computed flags.

        :param data: Packet contents dict.
        :return: Serialized TL bytes.
        """
        if self._pkt_schema is None:
            raise RuntimeError("TL schema 'adnl.packetContents' not found")
        return self.tl_schemas.serialize(self._pkt_schema, self._compute_flags(data))

    async def send_init_packet_raw(
        self,
        *,
        host: str,
        port: int,
        pub_key: bytes,
        messages: list[dict[str, t.Any]],
    ) -> _PeerState:
        """Send a signed ADNL init packet using raw parameters.

        :param host: Target IP address.
        :param port: Target UDP port.
        :param pub_key: Target Ed25519 public key (32 bytes).
        :param messages: ADNL message dicts (with ``@type``).
        :return: Peer state.
        """
        if not self._bound or self._udp_transport is None:
            raise NotConnectedError(
                component="AdnlUdpTransport",
                operation="send_init_packet",
            )

        peer = self.get_or_create_peer_raw(
            host=host,
            port=port,
            pub_key=pub_key,
        )
        sending_seqno = peer.seqno + 1

        ts = int(time.time())
        pub_schema = self.tl_schemas.get_by_name("pub.ed25519")
        if pub_schema is None:
            raise RuntimeError("TL schema 'pub.ed25519' not found")
        from_bytes = self.tl_schemas.serialize(
            pub_schema,
            {"key": self._local_pub.hex()},
        )

        data: dict[str, t.Any] = {
            "rand1": self._get_rand(),
            "from": from_bytes,
            "messages": messages,
            "address": {
                "addrs": [],
                "version": ts,
                "reinit_date": ts,
                "priority": 0,
                "expire_at": 0,
            },
            "seqno": sending_seqno,
            "confirm_seqno": peer.confirm_seqno,
            "recv_addr_list_version": ts,
            "reinit_date": ts,
            "dst_reinit_date": 0,
            "rand2": self._get_rand(),
        }

        serialized_unsigned = self._serialize_packet(data)
        signature = self._client.sign(serialized_unsigned)
        data["signature"] = signature
        serialized_signed = self._serialize_packet(data)

        checksum = hashlib.sha256(serialized_signed).digest()
        peer_server = Server(host, port, pub_key)
        shared_key = get_shared_key(
            self._client.x25519_private.encode(),
            peer_server.x25519_public.encode(),
        )
        cipher = create_aes_ctr_cipher(
            shared_key[0:16] + checksum[16:32],
            checksum[0:4] + shared_key[20:32],
        )
        encrypted = aes_ctr_encrypt(cipher, serialized_signed)

        packet = peer.peer_id + self._local_pub + checksum + encrypted
        self._udp_transport.sendto(packet, (host, port))
        peer.seqno = sending_seqno
        return peer

    async def send_channel_packet(
        self,
        peer: _PeerState,
        data: dict[str, t.Any],
    ) -> None:
        """Send an encrypted channel packet.

        :param peer: Target peer.
        :param data: Packet contents fields (messages, etc).
        """
        if not self._bound or self._udp_transport is None:
            raise NotConnectedError(
                component="AdnlUdpTransport",
                operation="send_channel_packet",
            )
        if peer.channel is None:
            raise TransportError(
                endpoint=peer.endpoint,
                operation="send_channel_packet",
                reason="no channel established",
            )

        sending_seqno = peer.seqno + 1
        data["rand1"] = self._get_rand()
        data["from_short"] = {"id": self._local_key_id.hex()}
        data["rand2"] = self._get_rand()
        data["seqno"] = sending_seqno
        data["confirm_seqno"] = peer.confirm_seqno

        serialized = self._serialize_packet(data)
        packet = peer.channel.encrypt(serialized)
        self._udp_transport.sendto(packet, (peer.host, peer.port))
        peer.seqno = sending_seqno

    def set_channel(self, peer: _PeerState, channel: AdnlChannel) -> None:
        """Register a confirmed channel for a peer.

        :param peer: Peer state.
        :param channel: Confirmed ADNL channel.
        """
        peer.channel = channel
        self._channels[channel.recv_id] = peer

    def reset_peer_channel(self, peer: _PeerState) -> None:
        """Remove channel for a peer, forcing re-establishment on next use.

        :param peer: Peer whose channel should be reset.
        """
        peer.channel = None
        stale = [rid for rid, ps in self._channels.items() if ps is peer]
        for rid in stale:
            del self._channels[rid]

    async def establish_channel(
        self,
        *,
        host: str,
        port: int,
        pub_key: bytes,
        extra_messages: list[dict[str, t.Any]] | None = None,
        timeout: float = 5.0,
    ) -> _PeerState:
        """Establish ADNL channel with a remote peer.

        Sends ``createChannel`` (+ optional extra messages) in a single
        init packet, waits for ``confirmChannel``, creates ``AdnlChannel``.

        :param host: Remote IP address.
        :param port: Remote UDP port.
        :param pub_key: Remote Ed25519 public key (32 bytes).
        :param extra_messages: Additional ADNL messages to bundle in init packet.
        :param timeout: Handshake timeout in seconds.
        :return: Peer state with established channel.
        """
        from tonutils.transports.adnl.channel import AdnlChannel as _AdnlChannel

        if not self._bound or self._udp_transport is None:
            raise NotConnectedError(
                component="AdnlUdpTransport",
                operation="establish_channel",
            )

        peer = self.get_or_create_peer_raw(host=host, port=port, pub_key=pub_key)
        if peer.channel is not None:
            return peer

        loop = asyncio.get_running_loop()
        ts = int(time.time())

        channel_client = Client(Client.generate_ed25519_private_key())
        channel_pub_hex = bytes(channel_client.ed25519_public).hex()

        create_channel_msg: dict[str, t.Any] = {
            "@type": "adnl.message.createChannel",
            "key": channel_pub_hex,
            "date": ts,
        }

        messages = [create_channel_msg]
        if extra_messages:
            messages.extend(extra_messages)

        channel_fut: asyncio.Future[t.Any] = loop.create_future()
        self._channel_pending[channel_pub_hex] = channel_fut

        try:
            await self.send_init_packet_raw(
                host=host,
                port=port,
                pub_key=pub_key,
                messages=messages,
            )

            try:
                confirm = await asyncio.wait_for(channel_fut, timeout=timeout)
            except asyncio.TimeoutError as exc:
                raise ProviderTimeoutError(
                    timeout=timeout,
                    endpoint=f"{host}:{port}",
                    operation="channel handshake",
                ) from exc

            peer_key = confirm.get("key", b"")
            if isinstance(peer_key, str):
                peer_key = bytes.fromhex(peer_key)

            channel_server = Server(host, port, peer_key)
            channel = _AdnlChannel(
                channel_client,
                channel_server,
                self._local_key_id,
                peer.peer_id,
            )
            self.set_channel(peer, channel)
            return peer

        finally:
            if channel_pub_hex in self._channel_pending:
                del self._channel_pending[channel_pub_hex]

    def resolve_channel_confirm(self, key_hex: str, msg: dict[str, t.Any]) -> bool:
        """Resolve a pending channel confirmation future.

        Called by the reader worker when ``adnl.message.confirmChannel``
        is received.

        :param key_hex: Channel public key hex (``peer_key`` field).
        :param msg: Full confirmChannel message dict.
        :return: ``True`` if a pending future was resolved.
        """
        fut = self._channel_pending.get(key_hex)
        if fut is not None and not fut.done():
            fut.set_result(msg)
            return True
        return False

    async def send_query_packet(
        self,
        peer: _PeerState,
        query_id: bytes,
        payload: bytes,
    ) -> None:
        """Send an ADNL query message through an established channel.

        :param peer: Peer with established channel.
        :param query_id: 32-byte random query identifier.
        :param payload: Serialized TL query bytes.
        """
        message: dict[str, t.Any] = {
            "@type": "adnl.message.query",
            "query_id": query_id.hex(),
            "query": payload,
        }
        await self.send_channel_packet(peer, {"messages": [message]})

    def decrypt_incoming(self, data: bytes) -> tuple[bytes, _PeerState | None]:
        """Decrypt a raw incoming UDP datagram.

        :param data: Raw datagram bytes.
        :return: Tuple of (decrypted payload, peer state or ``None``).
        """
        key_id = data[:32]

        peer_state = self._channels.get(key_id)
        if peer_state is not None and peer_state.channel is not None:
            checksum = data[32:64]
            encrypted = data[64:]
            plaintext = peer_state.channel.decrypt(encrypted, checksum)
            return plaintext, peer_state

        if key_id == self._local_key_id:
            sender_pub = data[32:64]
            checksum = data[64:96]
            encrypted = data[96:]

            peer_server = Server("", 0, sender_pub)
            shared_key = get_shared_key(
                self._client.x25519_private.encode(),
                peer_server.x25519_public.encode(),
            )
            cipher = create_aes_ctr_cipher(
                shared_key[0:16] + checksum[16:32],
                checksum[0:4] + shared_key[20:32],
            )
            plaintext = aes_ctr_decrypt(cipher, encrypted)
            if hashlib.sha256(plaintext).digest() != checksum:
                return b"", None
            return plaintext, None

        return b"", None

    async def recv_raw(self) -> tuple[bytes, tuple[str, int]]:
        """Receive a raw datagram from the UDP socket.

        :return: Tuple of (raw bytes, sender address).
        """
        return await self._incoming.get()

    def get_peer(self, endpoint: str) -> _PeerState | None:
        """Retrieve peer state by endpoint.

        :param endpoint: ``host:port`` string.
        :return: Peer state, or ``None``.
        """
        return self._peers.get(endpoint)

    async def close(self) -> None:
        """Close the UDP socket and clean up state."""
        self._bound = False
        self._peers.clear()
        self._channels.clear()

        for fut in self._channel_pending.values():
            if not fut.done():
                fut.cancel()
        self._channel_pending.clear()

        if self._udp_transport is not None:
            self._udp_transport.close()
            self._udp_transport = None
            self._protocol = None

        self._incoming = asyncio.Queue()
