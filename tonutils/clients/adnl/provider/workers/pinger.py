from __future__ import annotations

import asyncio
import typing as t

from pytoniq_core.crypto.ciphers import get_random

from tonutils.clients.adnl.provider.workers.base import BaseWorker

if t.TYPE_CHECKING:
    from tonutils.clients.adnl.provider import AdnlProvider


class PingerWorker(BaseWorker):
    """
    Periodic ping worker for ADNL providers.

    Sends lite-server ping requests at fixed intervals and records RTT metrics.
    """

    def __init__(
        self,
        provider: AdnlProvider,
        interval: int = 5,
    ) -> None:
        super().__init__(provider)
        self._interval = interval
        self._last_rtt: t.Optional[float] = None
        self._last_time: t.Optional[float] = None

    @property
    def last_time(self) -> t.Optional[float]:
        """Timestamp of the last successful ping."""
        return self._last_time

    @property
    def last_rtt(self) -> t.Optional[float]:
        """Round-trip time of the last ping in seconds."""
        return self._last_rtt

    @property
    def last_age(self) -> t.Optional[float]:
        """Age of the last ping result."""
        loop = self.provider.loop
        if loop is None or self._last_time is None:
            return None
        return loop.time() - self._last_time

    async def ping_once(self) -> None:
        """
        Perform a single lite-server ping request and measure RTT.

        Creates a pending ADNL future, sends ping packet and waits for reply.
        """
        if self.provider.loop is None:
            return

        random_id = int.from_bytes(get_random(8), "big", signed=True)
        payload = self.provider.tl_schemas.serialize(
            self.provider.tcp_ping_tl_schema,
            {"random_id": random_id},
        )
        fut = self.provider.loop.create_future()
        self.provider.pending[str(random_id)] = fut

        await self.provider.transport.send_adnl_packet(payload)

        start = self.provider.loop.time()
        await asyncio.wait_for(fut, timeout=self.provider.timeout)
        end = self.provider.loop.time()

        self._last_time = end
        self._last_rtt = end - start

    async def _run(self) -> None:
        """
        Periodically execute `ping_once()` while the worker is running.
        """
        while self.running:
            await asyncio.sleep(self._interval)

            if self.provider.is_connected:
                await self.ping_once()
