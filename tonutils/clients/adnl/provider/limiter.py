from __future__ import annotations

import asyncio

from pyapiq.limiter import AsyncLimiter


class PriorityLimiter(AsyncLimiter):

    def __init__(self, max_rate: int, time_period: float) -> None:
        super().__init__(max_rate, time_period)
        self._prio_waiters = 0

    async def acquire(self, priority: bool = False) -> None:
        if priority:
            async with self._lock:
                self._prio_waiters += 1

        try:
            while True:
                # noinspection PyUnresolvedReferences
                async with self._lock:
                    self._refill()
                    if self._tokens >= 1:
                        if not priority and self._prio_waiters > 0:
                            delay = self._time_period / self._max_rate
                        else:
                            self._tokens -= 1
                            return
                    else:
                        delay = self._time_period / self._max_rate
                await asyncio.sleep(delay)
        finally:
            if priority:
                async with self._lock:
                    self._prio_waiters -= 1
