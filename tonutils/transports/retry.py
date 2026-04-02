from __future__ import annotations

import asyncio
import typing as t

from tonutils.exceptions import ProviderResponseError, RetryLimitError

if t.TYPE_CHECKING:
    from tonutils.types import RetryPolicy

_T = t.TypeVar("_T")


async def send_with_retry(
    func: t.Callable[[], t.Awaitable[_T]],
    policy: RetryPolicy | None,
) -> _T:
    """Execute *func* with automatic retry governed by *policy*.

    :param func: Zero-argument async callable to attempt.
    :param policy: Retry policy, or ``None`` to disable retries.
    :return: Result of the first successful call.
    :raises ProviderResponseError: If no matching rule is found for the error.
    :raises RetryLimitError: If a matching rule exhausts its attempts or total timeout expires.
    """
    if policy is None:
        return await func()

    attempts: dict[int, int] = {}
    deadline: float | None = None

    if policy.total_timeout is not None:
        deadline = asyncio.get_event_loop().time() + policy.total_timeout

    while True:
        try:
            return await func()
        except ProviderResponseError as e:  # noqa: PERF203
            rule = policy.rule_for(e.code, e.message)
            if rule is None:
                raise

            key = id(rule)
            n = attempts.get(key, 0) + 1
            attempts[key] = n

            if n >= rule.max_retries:
                raise RetryLimitError(
                    attempts=n,
                    max_attempts=rule.max_retries,
                    last_error=e,
                ) from e

            delay = rule.delay_for_attempt(n - 1)

            if deadline is not None and asyncio.get_event_loop().time() + delay > deadline:
                raise RetryLimitError(
                    attempts=n,
                    max_attempts=rule.max_retries,
                    last_error=e,
                ) from e

            await asyncio.sleep(delay)
