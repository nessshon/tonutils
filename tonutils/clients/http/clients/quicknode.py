import typing as t

from aiohttp import ClientSession

from tonutils.clients.http.clients.toncenter import ToncenterClient
from tonutils.types import NetworkGlobalID, RetryPolicy


class QuicknodeClient(ToncenterClient):
    """Toncenter-compatible client using Quicknode as backend."""

    def __init__(
        self,
        *,
        http_provider_url: str,
        timeout: float = 10.0,
        session: t.Optional[ClientSession] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        cookies: t.Optional[t.Dict[str, str]] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> None:
        """
        :param http_provider_url: QuickNode TON HTTP endpoint URL.
            You can obtain a personal endpoint on the QuickNode website: https://www.quicknode.com/.
        :param timeout: Request timeout in seconds.
        :param session: External aiohttp session, or `None`.
        :param headers: Default headers for owned session.
        :param cookies: Default cookies for owned session.
        :param rps_limit: Requests-per-period limit, or `None`.
        :param rps_period: Rate limit period in seconds.
        :param retry_policy: Retry policy with per-error-code rules, or `None`.
        """
        super().__init__(
            network=NetworkGlobalID.MAINNET,
            base_url=http_provider_url,
            timeout=timeout,
            session=session,
            headers=headers,
            cookies=cookies,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )
