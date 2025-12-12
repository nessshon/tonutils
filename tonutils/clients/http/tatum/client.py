from __future__ import annotations

import typing as t

from aiohttp import ClientSession

from tonutils.clients.http.tatum.provider import TatumHttpProvider
from tonutils.clients.http.toncenter.client import ToncenterHttpClient
from tonutils.exceptions import ClientNotConnectedError
from tonutils.types import NetworkGlobalID


class TatumHttpClient(ToncenterHttpClient):
    """TON blockchain client using Tatum HTTP API as transport."""

    def __init__(
        self,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        api_key: str,
        base_url: t.Optional[str] = None,
        timeout: int = 10,
        session: t.Optional[ClientSession] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
    ) -> None:
        """
        Initialize Tatum HTTP client.

        :param network: Target TON network (mainnet or testnet)
        :param api_key: Tatum API key
            You can get an API key on the Tatum website: https://tatum.io/
        :param base_url: Optional custom Tatum base URL
        :param timeout: HTTP request timeout in seconds
        :param session: Optional externally managed aiohttp.ClientSession
        :param rps_limit: Optional requests-per-second limit
        :param rps_period: Time window in seconds for rate limiting
        :param rps_retries: Number of retries on rate limiting
        """
        super().__init__(network=network)
        self._provider: TatumHttpProvider = TatumHttpProvider(
            api_key=api_key,
            network=network,
            base_url=base_url,
            timeout=timeout,
            session=session,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
        )

    @property
    def provider(self) -> TatumHttpProvider:
        """
        Underlying Tatum HTTP provider.

        :return: TatumHttpProvider instance used for HTTP requests
        """
        if not self.is_connected:
            raise ClientNotConnectedError(self)
        return self._provider

    async def __aenter__(self) -> TatumHttpClient:
        await self._provider.__aenter__()
        return self
