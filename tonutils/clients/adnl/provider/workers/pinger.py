from __future__ import annotations

import asyncio
import typing as t

from pytoniq_core.crypto.ciphers import get_random

from tonutils.clients.adnl.provider.workers.base import BaseWorker

if t.TYPE_CHECKING:
    from tonutils.clients.adnl.provider import AdnlProvider


class PingerWorker(BaseWorker):

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
        return self._last_time

    @property
    def last_rtt(self) -> t.Optional[float]:
        return self._last_rtt

    @property
    def last_age(self) -> t.Optional[float]:
        loop = self.provider.loop
        if loop is None or self._last_time is None:
            return None
        return loop.time() - self._last_time

    async def ping_once(self) -> None:
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
        while self.running:
            await asyncio.sleep(self._interval)

            if self.provider.is_connected:
                await self.ping_once()
