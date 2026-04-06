from __future__ import annotations

import typing as t

from ton_core import NetworkGlobalID

from tonutils.clients.http.toncenter import ToncenterClient
from tonutils.exceptions import NetworkNotSupportedError
from tonutils.types import DEFAULT_REQUEST_TIMEOUT

if t.TYPE_CHECKING:
    from aiohttp import ClientSession

    from tonutils.types import RetryPolicy


class ChainstackClient(ToncenterClient):
    """Toncenter-compatible client using Chainstack as backend."""

    def __init__(
        self,
        network: NetworkGlobalID,
        *,
        http_provider_url: str,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        session: ClientSession | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        rps_limit: int | None = None,
        rps_period: float | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Initialize the Chainstack client.

        :param network: Target TON network.
        :param http_provider_url: Chainstack TON HTTP endpoint URL.
            You can obtain a personal endpoint on the Chainstack website: https://chainstack.com/.
        :param timeout: Request timeout in seconds.
        :param session: External aiohttp session, or ``None``.
        :param headers: Extra headers merged into every request.
        :param cookies: Extra cookies merged into every request.
        :param rps_limit: Requests-per-period cap, or ``None`` for automatic defaults.
        :param rps_period: Rate-limit window in seconds, or ``None`` for automatic defaults.
        :param retry_policy: Retry policy with per-status rules, or ``None``.
        """
        super().__init__(
            network=network,
            base_url=http_provider_url,
            timeout=timeout,
            session=session,
            headers=headers,
            cookies=cookies,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )


class QuicknodeClient(ToncenterClient):
    """Toncenter-compatible client using Quicknode as backend."""

    def __init__(
        self,
        *,
        http_provider_url: str,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        session: ClientSession | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        rps_limit: int | None = None,
        rps_period: float | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Initialize the QuickNode client.

        :param http_provider_url: QuickNode TON HTTP endpoint URL.
            You can obtain a personal endpoint on the QuickNode website: https://www.quicknode.com/.
        :param timeout: Request timeout in seconds.
        :param session: External aiohttp session, or ``None``.
        :param headers: Extra headers merged into every request.
        :param cookies: Extra cookies merged into every request.
        :param rps_limit: Requests-per-period cap, or ``None`` for automatic defaults.
        :param rps_period: Rate-limit window in seconds, or ``None`` for automatic defaults.
        :param retry_policy: Retry policy with per-status rules, or ``None``.
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


class TatumClient(ToncenterClient):
    """Toncenter-compatible client using Tatum as backend."""

    def __init__(
        self,
        network: NetworkGlobalID,
        *,
        api_key: str,
        base_url: str | None = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        session: ClientSession | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        rps_limit: int | None = None,
        rps_period: float | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Initialize the Tatum client.

        :param network: Target TON network.
        :param api_key: Tatum API key.
            You can get an API key on the Tatum website: https://tatum.io/.
        :param base_url: Custom endpoint base URL, or ``None``.
        :param timeout: Request timeout in seconds.
        :param session: External aiohttp session, or ``None``.
        :param headers: Extra headers merged into every request.
        :param cookies: Extra cookies merged into every request.
        :param rps_limit: Requests-per-period cap, or ``None`` for automatic defaults.
        :param rps_period: Rate-limit window in seconds, or ``None`` for automatic defaults.
        :param retry_policy: Retry policy with per-status rules, or ``None``.
        """
        urls = {
            NetworkGlobalID.MAINNET: "https://ton-mainnet.gateway.tatum.io",
            NetworkGlobalID.TESTNET: "https://ton-testnet.gateway.tatum.io",
        }
        base_url = base_url or urls.get(network)
        if base_url is None:
            raise NetworkNotSupportedError(network, provider="Tatum")

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
