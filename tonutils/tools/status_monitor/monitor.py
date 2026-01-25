from __future__ import annotations

import asyncio
import time
import typing as t

from tonutils.clients import LiteClient
from tonutils.clients.adnl.provider.models import GlobalConfig
from tonutils.tools.status_monitor.console import Console
from tonutils.tools.status_monitor.models import (
    BlockInfo,
    LiteServerStatus,
    LiteServer,
)
from tonutils.types import (
    NetworkGlobalID,
    WorkchainID,
    MAINNET_GENESIS_UTIME,
    MASTERCHAIN_SHARD,
)


class LiteServerMonitor:
    RENDER_INTERVAL = 0.1
    RECONNECT_INTERVAL = 30.0

    FAST_UPDATE_INTERVAL = 0.3
    MEDIUM_UPDATE_INTERVAL = 3.0
    SLOW_UPDATE_INTERVAL = 10.0

    def __init__(self, clients: t.List[LiteClient]) -> None:
        self._clients = clients
        self._console = Console()

        self._archive_cache: t.Dict[int, int] = {}
        self._statuses: t.Dict[int, LiteServerStatus] = {}
        self._last_connect: t.Dict[int, float] = {}

        self._tasks: t.List[asyncio.Task[None]] = []
        self._stop = asyncio.Event()

        self._locks: t.Dict[int, asyncio.Lock] = {}

    @classmethod
    def from_config(
        cls,
        config: GlobalConfig,
        network: NetworkGlobalID,
        rps_limit: t.Optional[int] = 100,
    ) -> LiteServerMonitor:
        return cls(
            [
                LiteClient(
                    network=network,
                    ip=server.host,
                    port=server.port,
                    public_key=server.id,
                    rps_limit=rps_limit,
                )
                for server in config.liteservers
            ]
        )

    @property
    def statuses(self) -> t.List[LiteServerStatus]:
        return list(self._statuses.values())

    async def run(self) -> None:
        self._console.enter()
        self._init_statuses()
        self._start_update_loops()

        try:
            while not self._stop.is_set():
                self._console.render(self.statuses)
                await self._sleep(self.RENDER_INTERVAL)
        finally:
            self._console.exit()

    async def stop(self) -> None:
        if self._stop.is_set():
            return
        self._stop.set()

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        close_tasks = [client.close() for client in self._clients]
        await asyncio.gather(*close_tasks, return_exceptions=True)

    def _init_statuses(self) -> None:
        for index, client in enumerate(self._clients):
            server = LiteServer(
                index=index,
                host=client.provider.node.host,
                port=client.provider.node.port,
            )
            self._statuses[index] = LiteServerStatus(server=server)
            self._locks[index] = asyncio.Lock()

    def _start_update_loops(self) -> None:
        if self._tasks:
            return

        for index, client in enumerate(self._clients):
            fast = self._fast_update_loop(index, client)
            self._tasks.append(asyncio.create_task(fast))

            medium = self._medium_update_loop(index, client)
            self._tasks.append(asyncio.create_task(medium))

            slow = self._slow_update_loop(index, client)
            self._tasks.append(asyncio.create_task(slow))

    async def _ensure_connected(self, index: int, client: LiteClient) -> bool:
        if client.provider.connected:
            return True

        now = time.monotonic()
        last_attempt = self._last_connect.get(index, 0.0)
        if now - last_attempt < self.RECONNECT_INTERVAL:
            return False

        self._last_connect[index] = now
        await self._connect(index, client)
        return client.provider.connected

    async def _fast_update_loop(self, index: int, client: LiteClient) -> None:
        while not self._stop.is_set():
            if not await self._ensure_connected(index, client):
                await self._sleep(1.0)
                continue

            await asyncio.gather(
                self._update_time(index, client),
                self._update_last_blocks(index, client),
                return_exceptions=True,
            )
            await self._sleep(self.FAST_UPDATE_INTERVAL)

    async def _medium_update_loop(self, index: int, client: LiteClient) -> None:
        while not self._stop.is_set():
            if not client.connected:
                await self._sleep(1.0)
                continue

            await asyncio.gather(
                self._update_ping_ms(index, client),
                self._update_request_ms(index, client),
                return_exceptions=True,
            )
            await self._sleep(self.MEDIUM_UPDATE_INTERVAL)

    async def _slow_update_loop(self, index: int, client: LiteClient) -> None:
        while not self._stop.is_set():
            if not client.connected:
                await self._sleep(1.0)
                continue

            await asyncio.gather(
                self._update_version(index, client),
                self._update_archive_from(index, client),
                return_exceptions=True,
            )
            await self._sleep(self.SLOW_UPDATE_INTERVAL)

    async def _sleep(self, seconds: float) -> None:
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            pass

    async def _set_status(self, index: int, **kwargs: t.Any) -> None:
        async with self._locks[index]:
            current = self._statuses[index]
            self._statuses[index] = current.model_copy(update=kwargs)

    async def _connect(self, index: int, client: LiteClient) -> None:
        try:
            start = time.perf_counter()
            await client.connect()
            connect_ms = int((time.perf_counter() - start) * 1000)
            await self._set_status(index, connect_ms=connect_ms, last_error=None)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_version(self, index: int, client: LiteClient) -> None:
        try:
            version = await client.get_version()
            await self._set_status(index, version=version)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_time(self, index: int, client: LiteClient) -> None:
        try:
            server_time = await client.get_time()
            await self._set_status(index, time=server_time)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_ping_ms(self, index: int, client: LiteClient) -> None:
        try:
            ping_ms = client.provider.last_ping_ms
            if ping_ms is not None:
                await self._set_status(index, ping_ms=ping_ms)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_request_ms(self, index: int, client: LiteClient) -> None:
        try:
            start = time.perf_counter()
            await client.get_masterchain_info()
            request_ms = int((time.perf_counter() - start) * 1000)
            await self._set_status(index, request_ms=request_ms)
        except Exception as e:
            await self._set_status(index, last_error=str(e))

    async def _update_last_blocks(self, index: int, client: LiteClient) -> None:
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
        cached: t.Optional[int] = None,
    ) -> int:
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
                await client.provider.lookup_block(
                    workchain=WorkchainID.MASTERCHAIN,
                    shard=MASTERCHAIN_SHARD,
                    utime=utime,
                )
                return True
            except (Exception,):
                return False

        while left <= right:
            mid = (left + right) // 2
            if await probe(mid):
                best_days = mid
                left = mid + 1
            else:
                right = mid - 1

        return now - best_days * seconds_per_day
