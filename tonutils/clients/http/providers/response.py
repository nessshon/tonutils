from __future__ import annotations

import json
import typing as t

import aiohttp

from tonutils.exceptions import ProviderResponseError, CDN_CHALLENGE_MARKERS


class HttpResponse:

    @classmethod
    async def read(cls, resp: aiohttp.ClientResponse) -> t.Any:
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
    def raise_error(
        cls,
        *,
        status: int,
        url: str,
        data: t.Any,
    ) -> None:
        exc = cls._detect_proxy_error(data, status=status, url=url)
        if exc is not None:
            raise exc

        message = cls._extract_error_message(data)
        raise ProviderResponseError(
            code=status,
            message=message,
            endpoint=url,
        )

    @classmethod
    def _detect_proxy_error(
        cls,
        data: t.Any,
        *,
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
