from __future__ import annotations

import asyncio
import typing as t

from ton_core import get_random

from tonutils.exceptions import (
    ClientError,
    NotConnectedError,
    ProviderError,
    ProviderTimeoutError,
    TransportError,
)
from tonutils.providers.dht.codec import DhtCodec
from tonutils.providers.dht.reader import DhtReaderWorker
from tonutils.transports.adnl.udp import AdnlUdpTransport

if t.TYPE_CHECKING:
    from ton_core import DhtNodeConfig

    from tonutils.clients.dht.models import DhtNode, DhtValue


class DhtProvider:
    """Kademlia DHT provider over ADNL UDP.

    Orchestrates queries through ``AdnlUdpTransport`` and delegates
    all TL serialization/parsing/verification to ``DhtCodec``.
    Channel establishment is handled entirely by the transport layer.
    """

    def __init__(
        self,
        *,
        nodes: list[DhtNodeConfig],
        k: int = 7,
        connect_timeout: float = 5.0,
        request_timeout: float = 3.0,
    ) -> None:
        """Initialize the DHT provider.

        :param nodes: DHT node configurations from global config.
        :param k: Kademlia replication parameter.
        :param connect_timeout: Timeout in seconds for initial node connection.
        :param request_timeout: Timeout in seconds for a single DHT query.
        """
        self._config_nodes = list(nodes)
        self._k = k
        self._connect_timeout = connect_timeout
        self._request_timeout = request_timeout

        self._transport = AdnlUdpTransport()
        self._codec = DhtCodec()
        self._reader = DhtReaderWorker(self)

        self._pending: dict[str, asyncio.Future[t.Any]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

        self._connected = False

    @property
    def transport(self) -> AdnlUdpTransport:
        """Shared ADNL-UDP transport."""
        return self._transport

    @property
    def codec(self) -> DhtCodec:
        """DHT protocol codec (TL serialization/parsing/verification)."""
        return self._codec

    @property
    def pending(self) -> dict[str, asyncio.Future[t.Any]]:
        """Pending futures dict (query_id hex → future)."""
        return self._pending

    @property
    def connected(self) -> bool:
        """``True`` if the transport is bound and at least one node connected."""
        return self._connected and self._transport.bound

    @property
    def local_key_id(self) -> bytes:
        """SHA-256 key ID of the local public key."""
        return self._transport.local_key_id

    @property
    def k(self) -> int:
        """Kademlia replication parameter."""
        return self._k

    @property
    def request_timeout(self) -> float:
        """Timeout in seconds for a single DHT query."""
        return self._request_timeout

    async def bind(self) -> None:
        """Bind UDP socket and start reader without connecting to nodes.

        Idempotent — safe to call multiple times.
        """
        if self._loop is not None:
            return

        self._loop = asyncio.get_running_loop()
        await self._transport.bind()
        await self._reader.start()

    async def connect(self) -> list[tuple[bytes, DhtNode]]:
        """Bind UDP socket, start reader, connect to initial nodes.

        :return: List of ``(adnl_id, DhtNode)`` pairs for successfully
            connected nodes.
        """
        if self._connected:
            return []

        await self.bind()

        tasks = [self._connect_initial_node(node) for node in self._config_nodes]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        connected_nodes: list[tuple[bytes, DhtNode]] = [r for r in results if isinstance(r, tuple) and len(r) == 2]

        if connected_nodes:
            self._connected = True

        return connected_nodes

    async def _connect_initial_node(
        self,
        node: DhtNodeConfig,
    ) -> tuple[bytes, DhtNode] | None:
        """Establish channel with an initial config node.

        :param node: DHT node configuration.
        :return: ``(adnl_id, DhtNode)`` on success, ``None`` on failure.
        """
        try:
            from tonutils.clients.dht.models import DhtNode as _DhtNode
            from tonutils.clients.dht.models import compute_key_id

            host = node.host
            port = node.port
            pub_key = node.pub_key
            adnl_id = compute_key_id(pub_key)

            dht_node = _DhtNode(
                adnl_id=adnl_id,
                addr=f"{host}:{port}",
                server_key=pub_key,
            )

            query_payload = self._codec.serialize_get_signed_address_list()
            query_id = get_random(32)
            query_msg: dict[str, t.Any] = {
                "@type": "adnl.message.query",
                "query_id": query_id.hex(),
                "query": query_payload,
            }

            query_fut: asyncio.Future[t.Any] = asyncio.get_running_loop().create_future()
            self._pending[query_id.hex()] = query_fut

            try:
                await asyncio.wait_for(
                    self._transport.establish_channel(
                        host=host,
                        port=port,
                        pub_key=pub_key,
                        extra_messages=[query_msg],
                        timeout=self._connect_timeout,
                    ),
                    timeout=self._connect_timeout + 1.0,
                )
                await asyncio.wait_for(query_fut, timeout=self._request_timeout)
            finally:
                query_id_hex = query_id.hex()
                if query_id_hex in self._pending:
                    del self._pending[query_id_hex]

            return adnl_id, dht_node

        except (OSError, TransportError, ProviderError, asyncio.TimeoutError):
            return None

    async def close(self) -> None:
        """Stop reader, cancel pending queries, and close transport."""
        self._connected = False
        await self._reader.stop()

        for fut in self._pending.values():
            if not fut.done():
                fut.cancel()
        self._pending.clear()

        await self._transport.close()
        self._loop = None

    async def ensure_channel(self, dht_node: DhtNode) -> None:
        """Ensure ADNL channel exists for a DHT node.

        Bundles a ``getSignedAddressList`` query in the init packet —
        ADNL-UDP servers require at least one query alongside
        ``createChannel`` to respond with ``confirmChannel``.
        """
        if self._loop is None:
            raise NotConnectedError(
                component="DhtProvider",
                operation="ensure_channel",
            )

        peer = self._transport.get_peer(dht_node.addr)
        if peer is not None and peer.channel is not None:
            return

        host, port_str = dht_node.addr.split(":")
        port = int(port_str)

        query_id = get_random(32)
        query_payload = self._codec.serialize_get_signed_address_list()
        query_msg: dict[str, t.Any] = {
            "@type": "adnl.message.query",
            "query_id": query_id.hex(),
            "query": query_payload,
        }

        query_fut: asyncio.Future[t.Any] = self._loop.create_future()
        self._pending[query_id.hex()] = query_fut

        try:
            await self._transport.establish_channel(
                host=host,
                port=port,
                pub_key=dht_node.server_key,
                extra_messages=[query_msg],
                timeout=self._connect_timeout,
            )
            await asyncio.wait_for(query_fut, timeout=self._request_timeout)
        finally:
            query_id_hex = query_id.hex()
            if query_id_hex in self._pending:
                del self._pending[query_id_hex]

    async def _reinit_node(self, dht_node: DhtNode) -> None:
        """Reset channel for a degraded node.

        Go parity: ``peer.Reinit()`` called when ``inFlyQueries == 0``
        and ``badScore > 1``.
        """
        peer = self._transport.get_peer(dht_node.addr)
        if peer is not None:
            self._transport.reset_peer_channel(peer)

    async def query_node(
        self,
        dht_node: DhtNode,
        request: bytes,
    ) -> dict[str, t.Any]:
        """Send a query to a node with channel auto-establishment.

        Tracks in-flight queries, uses ``reportLimit`` (timeout - 500ms)
        to avoid penalizing nodes for caller-imposed short deadlines,
        and calls reinit when all queries complete on a degraded node.

        :param dht_node: Target node.
        :param request: Serialized TL query bytes (from codec).
        :return: Decoded response dictionary.
        """
        if self._loop is None:
            raise NotConnectedError(
                component="DhtProvider",
                operation="query_node",
            )

        try:
            await self.ensure_channel(dht_node)
        except Exception:
            dht_node.update_status(False)
            raise

        peer = self._transport.get_peer(dht_node.addr)
        if peer is None or peer.channel is None:
            dht_node.update_status(False)
            raise ClientError(f"DhtProvider: no channel for {dht_node.addr}")

        query_id = get_random(32)
        query_id_hex = query_id.hex()

        fut: asyncio.Future[t.Any] = self._loop.create_future()
        self._pending[query_id_hex] = fut

        dht_node.inc_in_fly()
        start = self._loop.time()
        report_limit = start + self._request_timeout - 0.5
        try:
            await self._transport.send_query_packet(peer, query_id, request)

            try:
                resp = await asyncio.wait_for(fut, timeout=self._request_timeout)
            except asyncio.TimeoutError as exc:
                raise ProviderTimeoutError(
                    timeout=self._request_timeout,
                    endpoint=dht_node.addr,
                    operation="query",
                ) from exc
            rtt_ms = int((self._loop.time() - start) * 1000)

            dht_node.update_status(True)
            dht_node.ping = rtt_ms

            if not isinstance(resp, dict):
                raise ClientError(f"invalid response type: {type(resp).__name__}")
            return resp

        except Exception:
            if self._loop.time() > report_limit:
                dht_node.update_status(False)
            raise
        finally:
            remaining = dht_node.dec_in_fly()
            if remaining == 0 and dht_node.bad_score > 1:
                await self._reinit_node(dht_node)
            if query_id_hex in self._pending:
                del self._pending[query_id_hex]

    async def find_nodes(
        self,
        node: DhtNode,
        key: bytes,
        k: int,
    ) -> list[dict[str, t.Any]]:
        """Execute ``dht.findNode`` on a single node.

        :return: List of raw ``dht.node`` TL dicts.
        """
        data = self._codec.serialize_find_node(key, k)
        resp = await self.query_node(node, data)
        return self._codec.parse_nodes_from_response(resp)

    async def find_value_on_node(
        self,
        node: DhtNode,
        key: bytes,
        k: int,
    ) -> DhtValue | list[DhtNode] | None:
        """Execute ``dht.findValue`` on a single node.

        :return: ``DhtValue`` if found, ``list[DhtNode]`` if redirected,
            or ``None`` on parse failure.
        """
        data = self._codec.serialize_find_value(key, k)
        resp = await self.query_node(node, data)

        tl_type = resp.get("@type", "")

        if tl_type == "dht.valueFound":
            dht_value = self._codec.parse_value(resp.get("value", {}))
            if dht_value is not None and not dht_value.expired and self._codec.verify_value(dht_value, key):
                return dht_value
            return None

        raw_nodes = self._codec.parse_nodes_from_response(resp)
        parsed: list[DhtNode] = []
        for nd in raw_nodes:
            dht_node = self._codec.parse_node(nd)
            if dht_node is not None:
                parsed.append(dht_node)
        return parsed if parsed else None

    async def store_value_on_node(
        self,
        node: DhtNode,
        value: dict[str, t.Any],
    ) -> bool:
        """Execute ``dht.store`` on a single node.

        :return: ``True`` if stored successfully.
        """
        try:
            data = self._codec.serialize_store(value)
            await self.query_node(node, data)
            return True
        except Exception:
            return False

    async def get_signed_address_list(
        self,
        node: DhtNode,
    ) -> dict[str, t.Any]:
        """Execute ``dht.getSignedAddressList`` on a single node."""
        data = self._codec.serialize_get_signed_address_list()
        return await self.query_node(node, data)

    async def ping_node(self, node: DhtNode) -> None:
        """Execute ``dht.ping`` on a single node."""
        data = self._codec.serialize_ping()
        await self.query_node(node, data)
