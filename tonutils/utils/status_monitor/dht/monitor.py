from __future__ import annotations

import asyncio
import time
import typing as t

from ton_core import (
    NetworkGlobalID,
    get_mainnet_global_config,
    get_testnet_global_config,
)

from tonutils.clients.dht.client import DhtClient
from tonutils.utils.status_monitor.base import BaseMonitor
from tonutils.utils.status_monitor.dht.console import DhtConsole
from tonutils.utils.status_monitor.dht.models import DhtNodeStatus
from tonutils.utils.status_monitor.models import ServerInfo

if t.TYPE_CHECKING:
    from ton_core import GlobalConfig

__all__ = ["DhtMonitor"]


class DhtMonitor(BaseMonitor[DhtClient, DhtNodeStatus]):
    """Real-time DHT node health monitor with terminal UI."""

    FAST_UPDATE_INTERVAL = 1.0
    """Seconds between ping cycles."""

    MEDIUM_UPDATE_INTERVAL = 3.0
    """Seconds between ``dht.findNode`` cycles."""

    SLOW_UPDATE_INTERVAL = 10.0
    """Seconds between ``dht.getSignedAddressList`` cycles."""

    def __init__(
        self,
        clients: list[DhtClient],
        k: int = 7,
    ) -> None:
        """Initialize the DHT monitor.

        :param clients: DHT node clients to monitor.
        :param k: Kademlia replication parameter (for display).
        """
        super().__init__(clients=clients, console=DhtConsole())
        self._k = k

    @classmethod
    def from_config(
        cls,
        config: GlobalConfig,
    ) -> DhtMonitor:
        """Create monitor from a ``GlobalConfig``.

        :param config: Network configuration with DHT section.
        :return: Configured monitor instance.
        :raises ValueError: If no DHT section is present.
        """
        if config.dht is None:
            raise ValueError("DhtMonitor: no DHT section in config")

        nodes = config.dht.nodes
        k = config.dht.k

        clients = [
            DhtClient(
                host=node.host,
                port=node.port,
                public_key=node.pub_key,
            )
            for node in nodes
        ]
        return cls(clients=clients, k=k)

    @classmethod
    def from_network_config(
        cls,
        network: NetworkGlobalID,
    ) -> DhtMonitor:
        """Create monitor using global config from ton.org.

        :param network: Target TON network.
        :return: Configured monitor instance.
        """
        config_getters = {
            NetworkGlobalID.MAINNET: get_mainnet_global_config,
            NetworkGlobalID.TESTNET: get_testnet_global_config,
        }
        config = config_getters[network]()
        return cls.from_config(config)

    def _init_statuses(self) -> None:
        """Initialize status entries for all clients."""
        for index, client in enumerate(self._clients):
            server = ServerInfo(
                index=index,
                host=client.host,
                port=client.port,
            )
            self._statuses[index] = DhtNodeStatus(
                server=server,
                adnl_id=client.adnl_id.hex().upper(),
            )
            self._locks[index] = asyncio.Lock()

    def _is_connected(self, index: int) -> bool:
        """Check whether the DHT node at *index* is connected."""
        return self._clients[index].connected

    async def _connect(self, index: int) -> None:
        """Connect client and record RTT."""
        client = self._clients[index]
        try:
            start = time.perf_counter()
            await client.connect()
            connect_ms = int((time.perf_counter() - start) * 1000)
            await self._set_status(
                index,
                connect_ms=connect_ms,
                last_error=None,
            )
        except Exception as e:
            await self._set_status(
                index,
                connect_ms=None,
                ping_ms=None,
                request_ms=None,
                version=None,
                neighbors=None,
                last_error=str(e) or f"Connect: {type(e).__name__}",
            )

    async def _close_client(self, client: DhtClient) -> None:
        """Close a DHT client."""
        await client.close()

    async def _fast_update_loop(self, index: int) -> None:
        """Poll ``dht.ping`` at ``FAST_UPDATE_INTERVAL``."""
        while not self._stop.is_set():
            if not await self._ensure_connected(index):
                await self._sleep(1.0)
                continue

            await self._update_ping(index)
            await self._sleep(self.FAST_UPDATE_INTERVAL)

    async def _medium_update_loop(self, index: int) -> None:
        """Poll ``dht.findNode`` at ``MEDIUM_UPDATE_INTERVAL``."""
        while not self._stop.is_set():
            if not self._is_connected(index):
                await self._sleep(1.0)
                continue

            await self._update_find_node(index)
            await self._sleep(self.MEDIUM_UPDATE_INTERVAL)

    async def _slow_update_loop(self, index: int) -> None:
        """Poll ``dht.getSignedAddressList`` at ``SLOW_UPDATE_INTERVAL``."""
        while not self._stop.is_set():
            if not self._is_connected(index):
                await self._sleep(1.0)
                continue

            await self._update_version(index)
            await self._sleep(self.SLOW_UPDATE_INTERVAL)

    async def _update_ping(self, index: int) -> None:
        """Execute ``dht.ping`` and record latency."""
        client = self._clients[index]
        try:
            rtt = await client.ping()
            ping_ms = int(rtt * 1000)
            await self._set_status(index, ping_ms=ping_ms)
        except Exception as e:
            await self._set_status(
                index,
                last_error=str(e) or f"Ping: {type(e).__name__}",
            )

    async def _update_find_node(self, index: int) -> None:
        """Execute ``dht.findNode`` and record RTT and neighbor count."""
        client = self._clients[index]
        try:
            start = time.perf_counter()
            nodes_list = await client.find_nodes(
                client.provider.local_key_id,
                k=self._k,
            )
            request_ms = int((time.perf_counter() - start) * 1000)
            neighbors = f"{len(nodes_list)}/{self._k}"
            await self._set_status(
                index,
                request_ms=request_ms,
                neighbors=neighbors,
            )
        except Exception as e:
            await self._set_status(
                index,
                last_error=str(e) or f"FindNode: {type(e).__name__}",
            )

    async def _update_version(self, index: int) -> None:
        """Execute ``dht.getSignedAddressList`` and record version."""
        client = self._clients[index]
        node = client.node
        if node is None:
            return

        try:
            resp = await client.provider.get_signed_address_list(node)

            version = resp.get("version", 0)
            if version:
                await self._set_status(index, version=version)

        except Exception as e:
            await self._set_status(
                index,
                last_error=str(e) or f"GetAddrList: {type(e).__name__}",
            )
