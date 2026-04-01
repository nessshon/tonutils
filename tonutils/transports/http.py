from __future__ import annotations

import asyncio
import json
import typing as t
from typing import TypeVar

import aiohttp

from tonutils.exceptions import (
    CDN_CHALLENGE_MARKERS,
    NotConnectedError,
    ProviderError,
    ProviderResponseError,
    ProviderTimeoutError,
    RetryLimitError,
    TransportError,
)
from tonutils.transports.limiter import RateLimiter
from tonutils.types import BaseModel

_M = TypeVar("_M", bound=BaseModel)

if t.TYPE_CHECKING:
    from tonutils.types import RetryPolicy


class HttpTransport:
    """HTTP transport for TON API providers with rate limiting and retry."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 10.0,
        session: aiohttp.ClientSession | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        rps_limit: int | None = None,
        rps_period: float = 1.0,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Initialize the HTTP provider.

        :param base_url: Base endpoint URL without trailing slash.
        :param timeout: Request timeout in seconds.
        :param session: External aiohttp session, or ``None``.
        :param headers: Default headers for owned session.
        :param cookies: Default cookies for owned session.
        :param rps_limit: Requests-per-period limit, or ``None``.
        :param rps_period: Rate limit period in seconds.
        :param retry_policy: Retry policy with per-error-code rules, or ``None``.
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
    def limiter(self) -> RateLimiter | None:
        """Rate limiter instance, or ``None`` if not configured."""
        return self._limiter

    @property
    def session(self) -> aiohttp.ClientSession | None:
        """Underlying aiohttp session, or ``None`` if not connected."""
        return self._session

    @property
    def connected(self) -> bool:
        """``True`` if the session is initialized and open."""
        return self._session is not None and not self._session.closed

    @staticmethod
    def _model(model: type[_M], data: t.Any) -> _M:
        """Deserialize raw data into a model via ``from_dict``.

        :param model: Target model class with a ``from_dict`` class method.
        :param data: Raw data to deserialize.
        :return: Model instance.
        :raises ProviderError: If validation fails.
        """
        try:
            result = model.from_dict(data)
        except (TypeError, KeyError, ValueError) as e:
            raise ProviderError(
                f"invalid response: {model.__name__} validation failed"
            ) from e
        return t.cast("_M", result)

    async def send_http_request(
        self,
        method: str,
        path: str,
        *,
        params: t.Any = None,
        json_data: t.Any = None,
    ) -> t.Any:
        """Send an HTTP request with automatic retry.

        :param method: HTTP method.
        :param path: Endpoint path relative to base URL.
        :param params: Query parameters.
        :param json_data: JSON body.
        :return: Parsed response payload.
        """
        attempts: dict[int, int] = {}

        while True:
            try:
                return await self._send_once(
                    method,
                    path,
                    params=params,
                    json_data=json_data,
                )
            except ProviderResponseError as e:  # noqa: PERF203
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

    async def connect(self) -> None:
        """Initialize the HTTP session if not already connected."""
        if self.connected:
            return

        async with self._connect_lock:
            if self._session is not None and not self._session.closed:
                return

            self._session = aiohttp.ClientSession(
                headers=self._headers,
                cookies=self._cookies,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            )

    async def close(self) -> None:
        """Close the owned HTTP session and release resources."""
        async with self._connect_lock:
            if self._owns_session and self._session and not self._session.closed:
                await self._session.close()
            self._session = None

    @classmethod
    async def _read_response(cls, resp: aiohttp.ClientResponse) -> t.Any:
        """Read and decode an HTTP response body.

        :param resp: aiohttp response object.
        :return: Parsed JSON, plain string, or empty string.
        """
        body = await resp.read()
        if not body:
            return ""

        data = body.decode("utf-8", errors="replace").strip()
        if not data:
            return ""

        try:
            return json.loads(data)
        except Exception:
            return data

    @classmethod
    def _raise_error(cls, status: int, url: str, data: t.Any) -> None:
        """Raise ``ProviderResponseError`` from a failed HTTP response.

        :param status: HTTP status code.
        :param url: Request URL.
        :param data: Decoded response body.
        :raises ProviderResponseError: Always.
        """
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
        """Send a single HTTP request without retry.

        :param method: HTTP method.
        :param path: Endpoint path relative to base URL.
        :param params: Query parameters.
        :param json_data: JSON body.
        :return: Parsed response payload.
        """
        if not self.connected:
            raise NotConnectedError(
                component="HttpTransport",
                endpoint=self._base_url,
                operation=f"{method} {path}",
            )

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
            raise TransportError(
                endpoint=url,
                operation="http request",
                reason=str(exc),
            ) from exc

    @classmethod
    def _detect_proxy_error(
        cls,
        data: t.Any,
        status: int,
        url: str,
    ) -> ProviderResponseError | None:
        """Detect CDN/proxy challenge pages in response data.

        :param data: Decoded response body.
        :param status: HTTP status code.
        :param url: Request URL.
        :return: ``ProviderResponseError`` if a proxy marker is found, otherwise ``None``.
        """
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
        """Extract a human-readable error message from response data.

        :param data: Decoded response body (dict, list, str, or other).
        :return: Error message string.
        """
        if isinstance(data, dict):
            lowered = {k.lower(): v for k, v in data.items()}
            for key in ("error", "message", "detail", "description"):
                if key in lowered and isinstance(lowered[key], str):
                    return str(lowered[key])
            string_values = [str(v) for v in data.values() if isinstance(v, str)]
            return "; ".join(string_values) if string_values else str(data)

        if isinstance(data, list):
            return "; ".join(map(str, data))
        if isinstance(data, str):
            return data
        return repr(data)
