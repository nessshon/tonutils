import asyncio
import time


class RateLimiter:
    """
    Asynchronous token-bucket rate limiter with optional priority acquisition.

    Limits the number of acquire operations per time period and supports
    priority waiters that can bypass non-priority requests when tokens
    become available.
    """

    __slots__ = (
        "_max_rate",
        "_period",
        "_tokens",
        "_updated_at",
        "_cond",
        "_priority_waiters",
    )

    def __init__(self, max_rate: int, period: float = 1.0) -> None:
        """
        Initialize the rate limiter.

        :param max_rate: Maximum number of acquisitions allowed per period.
        :param period: Period length in seconds.
        :raises ValueError: If ``max_rate`` or ``period`` is not positive.
        """
        if max_rate <= 0:
            raise ValueError("max_rate must be > 0")
        if period <= 0:
            raise ValueError("period must be > 0")

        self._max_rate = max_rate
        self._period = period
        self._tokens = float(max_rate)
        self._updated_at = time.monotonic()
        self._cond = asyncio.Condition()
        self._priority_waiters = 0

    def when_ready(self) -> float:
        """
        Calculate delay until the next token becomes available.

        :return: Number of seconds to wait before a token can be acquired,
            or ``0`` if a token is available immediately.
        """
        now = time.monotonic()
        tokens = self._peek_tokens(now)
        if tokens >= 1.0:
            return 0.0
        return self._seconds_to_one_token(tokens)

    async def acquire(self, priority: bool = False) -> None:
        """
        Acquire a single token, waiting asynchronously if necessary.

        Priority acquisitions are allowed to bypass non-priority waiters
        when tokens become available.

        :param priority: Whether to acquire the token with priority.
        """
        if priority:
            async with self._cond:
                self._priority_waiters += 1

            try:
                await self._acquire(priority=True)
            finally:
                async with self._cond:
                    self._priority_waiters -= 1
                    self._cond.notify_all()
            return

        await self._acquire(priority=False)

    async def _acquire(self, priority: bool) -> None:
        while True:
            async with self._cond:
                now = time.monotonic()
                self._refill(now)

                if self._tokens >= 1.0 and (priority or self._priority_waiters == 0):
                    self._tokens -= 1.0
                    self._cond.notify_all()
                    return

                if self._tokens < 1.0:
                    timeout = self._seconds_to_one_token(self._tokens)
                    await asyncio.wait_for(self._cond.wait(), timeout=timeout)
                else:
                    await self._cond.wait()

    def _peek_tokens(self, now: float) -> float:
        elapsed = now - self._updated_at
        if elapsed <= 0.0:
            return self._tokens

        rate = self._max_rate / self._period
        tokens = self._tokens + elapsed * rate
        return min(float(self._max_rate), tokens)

    def _refill(self, now: float) -> None:
        self._tokens = self._peek_tokens(now)
        self._updated_at = now

    def _seconds_to_one_token(self, tokens: float) -> float:
        missing = 1.0 - tokens
        if missing <= 0.0:
            return 0.0

        rate = self._max_rate / self._period
        return missing / rate
