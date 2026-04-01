from __future__ import annotations

import asyncio
import time
import typing as t

from ton_core import (
    MAINNET_GENESIS_UTIME,
    MASTERCHAIN_SHARD,
    NetworkGlobalID,
    WorkchainID,
)

from tonutils.clients import LiteClient
from tonutils.utils.status_monitor.base import BaseMonitor
from tonutils.utils.status_monitor.lite.console import LiteConsole
from tonutils.utils.status_monitor.lite.models import (
    BlockInfo,
    LiteServerStatus,
)
from tonutils.utils.status_monitor.models import ServerInfo

if t.TYPE_CHECKING:
    from ton_core import GlobalConfig

    from tonutils.types import RetryPolicy

__all__ = ["LiteServerMonitor"]


class LiteServerMonitor(BaseMonitor[LiteClient, LiteServerStatus]):
    """Real-time liteserver health monitor with terminal UI."""

    FAST_UPDATE_INTERVAL = 0.3
    """Seconds between time and block update cycles."""

    MEDIUM_UPDATE_INTERVAL = 3.0
    """Seconds between ping and request RTT cycles."""

    SLOW_UPDATE_INTERVAL = 10.0
    """Seconds between version and archive depth cycles."""

    def __init__(self, clients: list[LiteClient]) -> None:
        """Initialize the liteserver monitor.

        :param clients: Liteserver clients to monitor.
        """
        super().__init__(clients=clients, console=LiteConsole())
        self._archive_cache: dict[int, int] = {}

    @classmethod
    def from_config(
        cls,
        config: GlobalConfig,
        network: NetworkGlobalID,
        rps_limit: int | None = 100,
        retry_policy: RetryPolicy | None = None,
    ) -> LiteServerMonitor:
        """Create monitor from a ``GlobalConfig``.

        :param config: Network configuration with liteserver list.
        :param network: Network identifier (mainnet / testnet).
        :param rps_limit: Requests-per-second limit per client, or ``None``.
        :param retry_policy: Retry policy for ADNL queries, or ``None``.
        :return: Configured monitor instance.
        """
        return cls(
            [
                LiteClient(
                    network=network,
                    ip=server.host,
                    port=server.port,
                    public_key=server.pub_key,
                    rps_limit=rps_limit,
                    retry_policy=retry_policy,
                )
                for server in config.liteservers
            ]
        )

    def _init_statuses(self) -> None:
        """Initialize status entries for all clients."""
        for index, client in enumerate(self._clients):
            server = ServerInfo(
                index=index,
                host=client.provider.node.host,
                port=client.provider.node.port,
            )
            self._statuses[index] = LiteServerStatus(server=server)
            self._locks[index] = asyncio.Lock()

    def _is_connected(self, index: int) -> bool:
        """Check whether the liteserver at *index* is connected."""
        return self._clients[index].provider.connected

    async def _connect(self, index: int) -> None:
        """Connect to liteserver and record RTT."""
        client = self._clients[index]
        try:
            start = time.perf_counter()
            await client.connect()
            connect_ms = int((time.perf_counter() - start) * 1000)
            await self._set_status(index, connect_ms=connect_ms, last_error=None)
        except Exception as e:
            await self._set_status(
                index,
                connect_ms=None,
                ping_ms=None,
                request_ms=None,
                version=None,
                time=None,
                last_mc_block=None,
                last_bc_block=None,
                archive_from=None,
                last_error=str(e),
            )

    async def _close_client(self, client: LiteClient) -> None:
        """Close a liteserver client."""
        await client.close()

    async def _fast_update_loop(self, index: int) -> None:
        """Poll time and blocks at ``FAST_UPDATE_INTERVAL``."""
        client = self._clients[index]
        while not self._stop.is_set():
            if not await self._ensure_connected(index):
                await self._sleep(1.0)
                continue

            await asyncio.gather(
                self._update_time(index, client),
                self._update_last_blocks(index, client),
                return_exceptions=True,
            )
            await self._sleep(self.FAST_UPDATE_INTERVAL)

    async def _medium_update_loop(self, index: int) -> None:
        """Poll ping and request RTT at ``MEDIUM_UPDATE_INTERVAL``."""
        client = self._clients[index]
        while not self._stop.is_set():
            if not self._is_connected(index):
                await self._sleep(1.0)
                continue

            await asyncio.gather(
                self._update_ping_ms(index, client),
                self._update_request_ms(index, client),
                return_exceptions=True,
            )
            await self._sleep(self.MEDIUM_UPDATE_INTERVAL)

    async def _slow_update_loop(self, index: int) -> None:
        """Poll version and archive depth at ``SLOW_UPDATE_INTERVAL``."""
        client = self._clients[index]
        while not self._stop.is_set():
            if not self._is_connected(index):
                await self._sleep(1.0)
                continue

            await asyncio.gather(
                self._update_version(index, client),
                self._update_archive_from(index, client),
                return_exceptions=True,
            )
            await self._sleep(self.SLOW_UPDATE_INTERVAL)

    async def _update_version(self, index: int, client: LiteClient) -> None:
        """Fetch and store server version."""
        try:
            version = await client.get_version()
            await self._set_status(index, version=version)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_time(self, index: int, client: LiteClient) -> None:
        """Fetch and store server time."""
        try:
            server_time = await client.get_time()
            await self._set_status(index, time=server_time)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_ping_ms(self, index: int, client: LiteClient) -> None:
        """Store last known ping latency."""
        try:
            ping_ms = client.provider.last_ping_ms
            if ping_ms is not None:
                await self._set_status(index, ping_ms=ping_ms)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_request_ms(self, index: int, client: LiteClient) -> None:
        """Measure and store a single request RTT."""
        try:
            start = time.perf_counter()
            await client.get_masterchain_info()
            request_ms = int((time.perf_counter() - start) * 1000)
            await self._set_status(index, request_ms=request_ms)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_last_blocks(self, index: int, client: LiteClient) -> None:
        """Fetch latest masterchain and basechain block info."""
        try:
            mc_block = client.provider.last_mc_block
            if mc_block is None:
                return

            mc_txs, shards = await asyncio.gather(
                client.get_block_transactions(mc_block),
                client.get_all_shards_info(mc_block),
            )
            last_mc_block = BlockInfo(seqno=mc_block.seqno, txs_count=len(mc_txs))

            if shards:
                bc_block = max(shards, key=lambda b: b.seqno)
                bc_txs = await client.get_block_transactions(bc_block)
                last_bc_block = BlockInfo(seqno=bc_block.seqno, txs_count=len(bc_txs))
                await self._set_status(
                    index,
                    last_mc_block=last_mc_block,
                    last_bc_block=last_bc_block,
                )
            else:
                await self._set_status(index, last_mc_block=last_mc_block)

        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_archive_from(self, index: int, client: LiteClient) -> None:
        """Binary-search for the earliest archived block timestamp."""
        try:
            now = int(time.time())
            result = await self._find_archive_depth(
                client, now, self._archive_cache.get(index)
            )
            self._archive_cache[index] = result
            await self._set_status(index, archive_from=result)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    @staticmethod
    async def _find_archive_depth(
        client: LiteClient,
        now: int,
        cached: int | None = None,
    ) -> int:
        """Find the earliest archive timestamp via binary search.

        :param client: Liteserver client.
        :param now: Current unix timestamp.
        :param cached: Previously found timestamp, or ``None``.
        :return: Earliest archive unix timestamp.
        """
        seconds_per_day = 86400
        seconds_diff = now - MAINNET_GENESIS_UTIME
        right = seconds_diff // seconds_per_day

        if cached is not None:
            cached_days = (now - cached) // seconds_per_day
            left = cached_days
            best_days = cached_days
        else:
            left = 0
            best_days = 0

        async def probe(days: int) -> bool:
            utime = now - days * seconds_per_day
            try:
                _, block = await client.provider.lookup_block(
                    workchain=WorkchainID.MASTERCHAIN,
                    shard=MASTERCHAIN_SHARD,
                    utime=utime,
                )
                return abs(block.info.gen_utime - utime) <= seconds_per_day
            except Exception:
                return False

        while left <= right:
            mid = (left + right) // 2
            if await probe(mid):
                best_days = mid
                left = mid + 1
            else:
                right = mid - 1

        return now - best_days * seconds_per_day
