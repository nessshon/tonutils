from __future__ import annotations

import typing as t

from aiohttp import ClientSession

from tonutils.clients.http.quicknode.provider import QuicknodeHttpProvider
from tonutils.clients.http.toncenter.client import ToncenterHttpClient
from tonutils.exceptions import ClientNotConnectedError
from tonutils.types import NetworkGlobalID


class QuicknodeHttpClient(ToncenterHttpClient):
    """TON blockchain client using Quicknode HTTP API as transport."""

    def __init__(
        self,
        *,
        http_provider_url: str,
        timeout: int = 10,
        session: t.Optional[ClientSession] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
    ) -> None:
        """
        Initialize QuickNode HTTP client.

        :param http_provider_url: QuickNode TON HTTP endpoint URL.
            You can obtain a personal endpoint on the QuickNode website: https://www.quicknode.com/
        :param timeout: HTTP request timeout in seconds
        :param session: Optional externally managed aiohttp.ClientSession
        :param rps_limit: Optional requests-per-second limit
        :param rps_period: Time window in seconds for rate limiting
        :param rps_retries: Number of retries on rate limiting
        """
        super().__init__(network=NetworkGlobalID.MAINNET)
        self._provider: QuicknodeHttpProvider = QuicknodeHttpProvider(
            http_provider_url=http_provider_url,
            timeout=timeout,
            session=session,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
        )

    @property
    def provider(self) -> QuicknodeHttpProvider:
        """
        Underlying QuickNode HTTP provider.

        :return: QuicknodeHttpProvider instance used for HTTP requests
        """
        if not self.is_connected:
            raise ClientNotConnectedError(self)
        return self._provider

    async def __aenter__(self) -> QuicknodeHttpClient:
        await self._provider.__aenter__()
        return self
