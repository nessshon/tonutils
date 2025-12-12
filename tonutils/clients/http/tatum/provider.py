import typing as t

from aiohttp import ClientSession

from tonutils.clients.http.toncenter.provider import ToncenterHttpProvider
from tonutils.types import NetworkGlobalID


class TatumHttpProvider(ToncenterHttpProvider):
    """Low-level HTTP provider for Tatum API."""

    version = ""

    def __init__(
        self,
        network: NetworkGlobalID,
        api_key: str,
        base_url: t.Optional[str] = None,
        timeout: int = 10,
        session: t.Optional[ClientSession] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: t.Optional[float] = None,
        rps_retries: t.Optional[int] = None,
    ) -> None:
        """
        Initialize Tatum HTTP provider.

        :param network: TON network selector (mainnet/testnet)
        :param api_key: Tatum API key
            You can get an API key on the Tatum website: https://tatum.io/
        :param base_url: Custom Tatum base URL, overrides default if provided
        :param timeout: HTTP request timeout in seconds
        :param session: Optional aiohttp.ClientSession, external or auto-created
        :param rps_limit: Requests-per-second rate limit
        :param rps_period: Time period window for rate limiting
        :param rps_retries: Number of retries on rate-limit errors
        """
        urls = {
            NetworkGlobalID.MAINNET: "https://ton-mainnet.gateway.tatum.io",
            NetworkGlobalID.TESTNET: "https://ton-testnet.gateway.tatum.io",
        }
        base_url = base_url or urls.get(network)

        super().__init__(
            api_key=api_key,
            network=network,
            base_url=base_url,
            timeout=timeout,
            session=session,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
        )
