import typing as t

from aiohttp import ClientSession

from tonutils.clients.http.toncenter.provider import ToncenterHttpProvider
from tonutils.types import NetworkGlobalID


class ChainstackHttpProvider(ToncenterHttpProvider):
    """Low-level HTTP provider for Chainstack API."""

    version = ""

    def __init__(
        self,
        network: NetworkGlobalID,
        http_provider_url: str,
        timeout: int = 10,
        session: t.Optional[ClientSession] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: t.Optional[float] = None,
        rps_retries: t.Optional[int] = None,
    ) -> None:
        """
        Initialize Chainstack HTTP provider.

        :param network: TON network selector (mainnet/testnet)
        :param http_provider_url: Chainstack TON HTTP endpoint URL
            You can obtain a personal endpoint on the Chainstack website: https://chainstack.com/
        :param timeout: HTTP request timeout in seconds
        :param session: Optional aiohttp.ClientSession, external or auto-created
        :param rps_limit: Requests-per-second rate limit
        :param rps_period: Time period window for rate limiting
        :param rps_retries: Number of retries on rate-limit errors
        """
        super().__init__(
            network=network,
            base_url=http_provider_url,
            timeout=timeout,
            session=session,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
        )
