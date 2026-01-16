from __future__ import annotations

import asyncio
import typing as t

import aiohttp

from tonutils.clients.http.providers.response import HttpResponse
from tonutils.clients.limiter import RateLimiter
from tonutils.exceptions import (
    NotConnectedError,
    ProviderResponseError,
    ProviderTimeoutError,
    RetryLimitError,
)
from tonutils.types import RetryPolicy


class HttpProvider:
    """HTTP-based provider for TON HTTP APIs."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 10.0,
        session: t.Optional[aiohttp.ClientSession] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        cookies: t.Optional[t.Dict[str, str]] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> None:
        """Initialize HTTP provider.

        :param base_url: Base endpoint URL without trailing slash.
        :param timeout: Total request timeout in seconds.
        :param session: Optional external aiohttp session.
        :param headers: Default headers for owned session.
        :param cookies: Default cookies for owned session.
        :param rps_limit: Optional requests-per-period limit.
        :param rps_period: Rate limit period in seconds.
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = headers
        self._cookies = cookies

        self._session = session
        self._owns_session = session is None

        self._limiter = (
            RateLimiter(max_rate=rps_limit, period=rps_period)
            if rps_limit is not None
            else None
        )
        self._retry_policy = retry_policy
        self._connect_lock = asyncio.Lock()

    @property
    def session(self) -> t.Optional[aiohttp.ClientSession]:
        """Underlying aiohttp session, or None if not connected."""
        return self._session

    @property
    def is_connected(self) -> bool:
        """Check whether the provider session is initialized and open."""
        return self._session is not None and not self._session.closed

    async def connect(self) -> None:
        """Initialize HTTP session if not already connected."""
        if self.is_connected:
            return

        async with self._connect_lock:
            if self.is_connected:
                return

            self._session = aiohttp.ClientSession(
                headers=self._headers,
                cookies=self._cookies,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            )

    async def close(self) -> None:
        """Close owned HTTP session and release resources."""
        async with self._connect_lock:
            if self._owns_session and self._session and not self._session.closed:
                await self._session.close()
            self._session = None

    async def _send_once(
        self,
        method: str,
        path: str,
        *,
        params: t.Any = None,
        json_data: t.Any = None,
    ) -> t.Any:
        """Send a single HTTP request.

        Performs exactly one request attempt:
        - applies rate limiting if configured
        - converts network and protocol errors into provider exceptions

        :param method: HTTP method (GET, POST, etc.).
        :param path: Endpoint path relative to base_url.
        :param params: Optional query parameters.
        :param json_data: Optional JSON body.
        :return: Parsed response payload.
        """
        if not self.is_connected:
            raise NotConnectedError()

        assert self._session is not None
        url = f"{self._base_url}/{path.lstrip('/')}"

        try:
            if self._limiter:
                await self._limiter.acquire()

            async with self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
            ) as resp:
                data = await HttpResponse.read(resp)
                if resp.status >= 400:
                    HttpResponse.raise_error(
                        status=int(resp.status),
                        url=url,
                        data=data,
                    )
                return data

        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError(
                timeout=self._timeout,
                endpoint=url,
                operation="http request",
            ) from exc

        except aiohttp.ClientError as exc:
            raise ProviderResponseError(
                code=0,
                message=str(exc),
                endpoint=url,
            ) from exc

    async def send_http_request(
        self,
        method: str,
        path: str,
        *,
        params: t.Any = None,
        json_data: t.Any = None,
    ) -> t.Any:
        """Send an HTTP request with retry handling.

        On provider error, retries the request according to the retry policy
        matched by error code and message. If no rule matches, or retry attempts
        are exhausted, the error is raised.

        :param method: HTTP method.
        :param path: Endpoint path relative to base_url.
        :param params: Optional query parameters.
        :param json_data: Optional JSON body.
        :return: Parsed response payload.
        """
        attempts: t.Dict[int, int] = {}

        while True:
            try:
                return await self._send_once(
                    method,
                    path,
                    params=params,
                    json_data=json_data,
                )
            except ProviderResponseError as e:
                policy = self._retry_policy
                if policy is None:
                    raise

                rule = policy.rule_for(e.code, e.message)
                if rule is None:
                    raise

                key = id(rule)
                attempts[key] = attempts.get(key, 0) + 1

                if attempts[key] >= rule.attempts:
                    raise RetryLimitError(
                        attempts=attempts[key],
                        max_attempts=rule.attempts,
                        last_error=e,
                    ) from e

                await asyncio.sleep(rule.delay(attempts[key] - 1))
