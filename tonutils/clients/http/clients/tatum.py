import typing as t

from aiohttp import ClientSession

from tonutils.clients.http.clients.toncenter import ToncenterClient
from tonutils.types import NetworkGlobalID, RetryPolicy


class TatumClient(ToncenterClient):

    def __init__(
        self,
        network: NetworkGlobalID,
        *,
        api_key: str,
        base_url: t.Optional[str] = None,
        timeout: float = 10.0,
        session: t.Optional[ClientSession] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        cookies: t.Optional[t.Dict[str, str]] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> None:
        """
        Initialize Tatum HTTP client.

        :param network: Target TON network (mainnet or testnet)
        :param api_key: Tatum API key
            You can get an API key on the Tatum website: https://tatum.io/
        :param base_url: Optional custom Tatum base URL
        :param timeout: Total request timeout in seconds.
        :param session: Optional external aiohttp session.
        :param headers: Default headers for owned session.
        :param cookies: Default cookies for owned session.
        :param rps_limit: Optional requests-per-period limit.
        :param rps_period: Rate limit period in seconds.
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        """
        urls = {
            NetworkGlobalID.MAINNET: "https://ton-mainnet.gateway.tatum.io",
            NetworkGlobalID.TESTNET: "https://ton-testnet.gateway.tatum.io",
        }
        base_url = base_url or urls.get(network)
        super().__init__(
            network=network,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            session=session,
            headers=headers,
            cookies=cookies,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )
