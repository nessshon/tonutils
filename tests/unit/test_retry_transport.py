from __future__ import annotations

import pytest

from tonutils.exceptions import ProviderResponseError, RetryLimitError
from tonutils.transports.retry import send_with_retry
from tonutils.types import RetryPolicy, RetryRule


def _make_error(code: int = 429, message: str = "") -> ProviderResponseError:
    return ProviderResponseError(code=code, message=message, endpoint="test")


def _make_func(errors: list[ProviderResponseError], result: object = "ok"):
    calls = iter([*errors, None])

    async def func():
        err = next(calls)
        if err is not None:
            raise err
        return result

    return func


class TestNoPolicy:
    async def test_single_call_no_retry(self):
        result = await send_with_retry(_make_func([]), None)
        assert result == "ok"

    async def test_raises_immediately(self):
        with pytest.raises(ProviderResponseError):
            await send_with_retry(_make_func([_make_error()]), None)


class TestUnmatchedError:
    async def test_raises_without_retry(self):
        policy = RetryPolicy(rules=(RetryRule(codes=frozenset({429}), max_retries=3),))
        with pytest.raises(ProviderResponseError) as exc_info:
            await send_with_retry(_make_func([_make_error(code=999)]), policy)
        assert exc_info.value.code == 999


class TestMatchedRetry:
    async def test_retries_and_succeeds(self):
        policy = RetryPolicy(rules=(RetryRule(codes=frozenset({429}), max_retries=3, base_delay=0),))
        result = await send_with_retry(_make_func([_make_error(429), _make_error(429)], result="success"), policy)
        assert result == "success"

    async def test_exhausts_max_retries(self):
        policy = RetryPolicy(rules=(RetryRule(codes=frozenset({429}), max_retries=2, base_delay=0),))
        with pytest.raises(RetryLimitError) as exc_info:
            await send_with_retry(_make_func([_make_error(429)] * 5), policy)
        assert exc_info.value.attempts == 2
        assert exc_info.value.max_attempts == 2

    async def test_per_rule_attempt_tracking(self):
        rule_429 = RetryRule(codes=frozenset({429}), max_retries=2, base_delay=0)
        rule_503 = RetryRule(codes=frozenset({503}), max_retries=2, base_delay=0)
        policy = RetryPolicy(rules=(rule_429, rule_503))
        func = _make_func([_make_error(429), _make_error(503), _make_error(503)], result="ok")
        with pytest.raises(RetryLimitError) as exc_info:
            await send_with_retry(func, policy)
        assert isinstance(exc_info.value.last_error, ProviderResponseError)
        assert exc_info.value.last_error.code == 503


class TestDeadline:
    async def test_total_timeout_enforced(self):
        policy = RetryPolicy(
            rules=(RetryRule(codes=frozenset({429}), max_retries=100, base_delay=0.5),),
            total_timeout=0.1,
        )
        with pytest.raises(RetryLimitError):
            await send_with_retry(_make_func([_make_error(429)] * 100), policy)


class TestLastError:
    async def test_retry_limit_preserves_last_error(self):
        policy = RetryPolicy(rules=(RetryRule(codes=frozenset({429}), max_retries=1, base_delay=0),))
        err = _make_error(429, "rate limited")
        with pytest.raises(RetryLimitError) as exc_info:
            await send_with_retry(_make_func([err]), policy)
        assert exc_info.value.last_error is err
        assert isinstance(exc_info.value.last_error, ProviderResponseError)
        assert exc_info.value.last_error.message == "rate limited"
