from __future__ import annotations

import asyncio
import typing as t

from ton_core import get_random

from tonutils.transports.worker import BaseWorker

if t.TYPE_CHECKING:
    from tonutils.providers.lite.provider import LiteProvider


class PingerWorker(BaseWorker):
    """Periodic ping worker for ADNL providers.

    Sends lite-server ping requests at fixed intervals and records RTT.
    """

    def __init__(
        self,
        provider: LiteProvider,
        interval: int = 5,
    ) -> None:
        """Initialize the pinger worker.

        :param provider: Parent ADNL provider.
        :param interval: Ping interval in seconds.
        """
        super().__init__(provider)
        self._interval = interval
        self._last_rtt: float | None = None
        self._last_time: float | None = None

    @property
    def last_time(self) -> float | None:
        """Timestamp of the last successful ping."""
        return self._last_time

    @property
    def last_rtt(self) -> float | None:
        """Round-trip time of the last ping in seconds."""
        return self._last_rtt

    @property
    def last_age(self) -> float | None:
        """Age of the last ping result."""
        loop = self.provider.loop
        if loop is None or self._last_time is None:
            return None
        return float(loop.time() - self._last_time)

    async def ping_once(self) -> None:
        """Perform a single lite-server ping and measure RTT."""
        if self.provider.loop is None:
            return

        random_id = int.from_bytes(get_random(8), "big", signed=True)
        key = str(random_id)
        assert self.provider.tcp_ping_tl_schema is not None
        payload = self.provider.tl_schemas.serialize(
            self.provider.tcp_ping_tl_schema,
            {"random_id": random_id},
        )
        fut = self.provider.loop.create_future()
        self.provider.pending[key] = fut

        await self.provider.transport.send_adnl_packet(payload)

        try:
            start = self.provider.loop.time()
            await asyncio.wait_for(fut, timeout=self.provider.request_timeout)
            end = self.provider.loop.time()

            self._last_time = end
            self._last_rtt = end - start
        except asyncio.TimeoutError:
            pass
        finally:
            self.provider.pending.pop(key, None)

    async def _run(self) -> None:
        """Periodically execute ``ping_once`` while the worker is running."""
        while self.running:
            await asyncio.sleep(self._interval)

            if self.provider.connected:
                try:
                    await self.ping_once()
                except Exception:
                    continue
