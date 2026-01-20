from __future__ import annotations

import asyncio
import json
import typing as t

import aiohttp

from tonutils.clients.limiter import RateLimiter
from tonutils.exceptions import (
    NotConnectedError,
    ProviderResponseError,
    ProviderTimeoutError,
    RetryLimitError,
    CDN_CHALLENGE_MARKERS,
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

    @classmethod
    async def _read_response(cls, resp: aiohttp.ClientResponse) -> t.Any:
        body = await resp.read()
        if not body:
            return ""

        data = body.decode("utf-8", errors="replace").strip()
        if not data:
            return ""

        try:
            return json.loads(data)
        except (Exception,):
            return data

    @classmethod
    def _raise_error(cls, status: int, url: str, data: t.Any) -> None:
        exc = cls._detect_proxy_error(data, status=status, url=url)
        if exc is not None:
            raise exc

        message = cls._extract_error_message(data)
        raise ProviderResponseError(
            code=status,
            message=message,
            endpoint=url,
        )

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
                data = await self._read_response(resp)
                if resp.status >= 400:
                    self._raise_error(int(resp.status), url, data)
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

    @classmethod
    def _detect_proxy_error(
        cls,
        data: t.Any,
        status: int,
        url: str,
    ) -> t.Optional[ProviderResponseError]:
        body = (
            " ".join(str(v) for v in data.values())
            if isinstance(data, dict)
            else str(data)
        ).lower()

        for marker, message in CDN_CHALLENGE_MARKERS.items():
            if marker in body:
                return ProviderResponseError(
                    code=status,
                    message=message,
                    endpoint=url,
                )

        return None

    @staticmethod
    def _extract_error_message(data: t.Any) -> str:
        if isinstance(data, dict):
            lowered = {k.lower(): v for k, v in data.items()}
            for key in ("error", "message", "detail", "description"):
                if key in lowered and isinstance(lowered[key], str):
                    return lowered[key]
            string_values = [str(v) for v in data.values() if isinstance(v, str)]
            return "; ".join(string_values) if string_values else str(data)

        if isinstance(data, list):
            return "; ".join(map(str, data))
        if isinstance(data, str):
            return data
        return repr(data)
