from __future__ import annotations

import typing as t

from aiohttp import ClientSession

from tonutils.clients.http.quicknode.provider import QuicknodeHttpProvider
from tonutils.clients.http.toncenter.client import ToncenterHttpClient
from tonutils.exceptions import ClientNotConnectedError
from tonutils.types import NetworkGlobalID


class QuicknodeHttpClient(ToncenterHttpClient):

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
        if not self.is_connected:
            raise ClientNotConnectedError(self)
        return self._provider

    async def __aenter__(self) -> QuicknodeHttpClient:
        await self._provider.__aenter__()
        return self
