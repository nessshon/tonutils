import asyncio
import time


class RateLimiter:
    """
    Asynchronous token-bucket rate limiter with priority support.

    Priority requests are served before non-priority requests when
    tokens become available.
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
        :raises ValueError: If max_rate or period is not positive.
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

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._updated_at
        if elapsed > 0:
            rate = self._max_rate / self._period
            self._tokens = min(float(self._max_rate), self._tokens + elapsed * rate)
            self._updated_at = now

    def _seconds_to_token(self) -> float:
        """Calculate seconds until next token is available."""
        if self._tokens >= 1.0:
            return 0.0
        missing = 1.0 - self._tokens
        rate = self._max_rate / self._period
        return missing / rate

    async def acquire(self, priority: bool = False) -> None:
        """
        Acquire a single token, waiting if necessary.

        Priority requests bypass non-priority waiters when tokens
        become available.

        :param priority: Whether to acquire with priority.
        """
        async with self._cond:
            is_waiting = False

            try:
                while True:
                    self._refill()

                    # Check if token available
                    if self._tokens >= 1.0:
                        # Priority always takes; non-priority only if no priority waiting
                        if priority or self._priority_waiters == 0:
                            self._tokens -= 1.0
                            self._cond.notify_all()
                            return

                    # Register as priority waiter only when actually waiting
                    if priority and not is_waiting:
                        self._priority_waiters += 1
                        is_waiting = True

                    # Wait for token
                    wait_time = self._seconds_to_token()
                    if wait_time > 0:
                        try:
                            await asyncio.wait_for(self._cond.wait(), timeout=wait_time)
                        except asyncio.TimeoutError:
                            pass  # Expected — token should be ready now
                    else:
                        # Token available but blocked by priority — wait for notify
                        await self._cond.wait()

            finally:
                if is_waiting:
                    self._priority_waiters -= 1
                    self._cond.notify_all()

    def when_ready(self) -> float:
        """
        Calculate delay until the next token becomes available.

        :return: Seconds to wait, or 0 if ready immediately.
        """
        now = time.monotonic()
        elapsed = now - self._updated_at
        rate = self._max_rate / self._period
        tokens = min(float(self._max_rate), self._tokens + elapsed * rate)

        if tokens >= 1.0:
            return 0.0
        return (1.0 - tokens) / rate
