from __future__ import annotations

import asyncio

from pyapiq.limiter import AsyncLimiter


class PriorityLimiter(AsyncLimiter):
    """
    Token-bucket limiter with priority scheduling.

    Extends AsyncLimiter by allowing priority acquisitions that bypass
    normal waiters while still respecting rate limits.
    """

    def __init__(self, max_rate: int, time_period: float) -> None:
        """
        Initialize priority-aware limiter.

        :param max_rate: Maximum number of operations allowed in the window
        :param time_period: Time window length in seconds
        """
        super().__init__(max_rate, time_period)
        self._prio_waiters = 0

    async def acquire(self, priority: bool = False) -> None:
        """
        Acquire a limiter token.

        Priority requests are allowed to skip regular waiters when
        tokens become available.

        :param priority: Whether this acquisition request has priority
        """
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
