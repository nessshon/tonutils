from __future__ import annotations

import asyncio
import time

import pytest

from tonutils.transports.limiter import RateLimiter


class TestValidation:
    def test_max_rate_must_be_positive(self):
        with pytest.raises(ValueError):
            RateLimiter(max_rate=0)

    def test_period_must_be_positive(self):
        with pytest.raises(ValueError):
            RateLimiter(max_rate=1, period=0)


class TestAcquire:
    async def test_immediate_when_tokens_available(self):
        limiter = RateLimiter(max_rate=5, period=1.0)
        start = time.monotonic()
        await limiter.acquire()
        assert time.monotonic() - start < 0.05

    async def test_blocks_when_exhausted(self):
        limiter = RateLimiter(max_rate=1, period=0.5)
        await limiter.acquire()
        start = time.monotonic()
        await limiter.acquire()
        assert time.monotonic() - start >= 0.4

    async def test_respects_rate(self):
        limiter = RateLimiter(max_rate=2, period=1.0)
        await limiter.acquire()
        await limiter.acquire()
        start = time.monotonic()
        await limiter.acquire()
        assert time.monotonic() - start >= 0.4


class TestPriority:
    async def test_priority_before_normal(self):
        limiter = RateLimiter(max_rate=1, period=0.3)
        await limiter.acquire()

        results: list[str] = []

        async def normal():
            await limiter.acquire()
            results.append("normal")

        async def priority():
            await asyncio.sleep(0.05)
            await limiter.acquire(priority=True)
            results.append("priority")

        await asyncio.gather(normal(), priority())
        assert results[0] == "priority"


class TestWhenReady:
    def test_zero_when_available(self):
        limiter = RateLimiter(max_rate=5, period=1.0)
        assert limiter.when_ready() == 0.0

    async def test_positive_when_exhausted(self):
        limiter = RateLimiter(max_rate=1, period=1.0)
        await limiter.acquire()
        delay = limiter.when_ready()
        assert 0 < delay <= 1.0
