from __future__ import annotations

import typing as t

from aiohttp import ClientSession

from tonutils.clients.http.chainstack.provider import ChainstackHttpProvider
from tonutils.clients.http.toncenter.client import ToncenterHttpClient
from tonutils.exceptions import ClientNotConnectedError
from tonutils.types import NetworkGlobalID


class ChainstackHttpClient(ToncenterHttpClient):
    """TON blockchain client using Chainstack HTTP API as transport."""

    def __init__(
        self,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        http_provider_url: str,
        timeout: int = 10,
        session: t.Optional[ClientSession] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
    ) -> None:
        """
        Initialize Chainstack HTTP client.

        :param network: Target TON network (mainnet or testnet)
        :param http_provider_url: Chainstack TON HTTP endpoint URL
            You can obtain a personal endpoint on the Chainstack website: https://chainstack.com/
        :param timeout: HTTP request timeout in seconds
        :param session: Optional externally managed aiohttp.ClientSession
        :param rps_limit: Optional requests-per-second limit
        :param rps_period: Time window in seconds for rate limiting
        :param rps_retries: Number of retries on rate limiting
        """
        super().__init__(network=network)
        self._provider: ChainstackHttpProvider = ChainstackHttpProvider(
            network=network,
            http_provider_url=http_provider_url,
            timeout=timeout,
            session=session,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
        )

    @property
    def provider(self) -> ChainstackHttpProvider:
        """
        Underlying Chainstack HTTP provider.

        :return: ChainstackHttpProvider instance used for HTTP requests
        """
        if not self.is_connected:
            raise ClientNotConnectedError(self)
        return self._provider

    async def __aenter__(self) -> ChainstackHttpClient:
        await self._provider.__aenter__()
        return self
