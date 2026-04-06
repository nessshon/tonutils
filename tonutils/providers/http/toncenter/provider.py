from dataclasses import asdict

import aiohttp
from ton_core import NetworkGlobalID

from tonutils.exceptions import NetworkNotSupportedError
from tonutils.providers.http.toncenter.models import (
    GetAddressInformationResult,
    GetConfigAllResult,
    GetTransactionsResult,
    RunGetMethodPayload,
    RunGetMethodResult,
    SendBocPayload,
)
from tonutils.transports.http import HttpTransport
from tonutils.types import DEFAULT_REQUEST_TIMEOUT, RetryPolicy


class ToncenterHttpProvider(HttpTransport):
    """HTTP provider for the Toncenter API."""

    def __init__(
        self,
        network: NetworkGlobalID,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        session: aiohttp.ClientSession | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | None = None,
        rps_limit: int | None = None,
        rps_period: float = 1.0,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Initialize the Toncenter HTTP provider.

        :param network: Target TON network.
        :param api_key: API key, or ``None`` for keyless access with default rate limits.
        :param base_url: Custom endpoint base URL, or ``None``.
        :param timeout: Request timeout in seconds.
        :param session: External aiohttp session, or ``None``.
        :param headers: Extra headers merged into every request.
        :param cookies: Extra cookies merged into every request.
        :param rps_limit: Requests-per-period cap, or ``None`` for automatic defaults.
        :param rps_period: Rate-limit window in seconds.
        :param retry_policy: Retry policy with per-status rules, or ``None``.
        """
        urls = {
            NetworkGlobalID.MAINNET: "https://toncenter.com/api/v2",
            NetworkGlobalID.TESTNET: "https://testnet.toncenter.com/api/v2",
        }
        base_url = base_url or urls.get(network)
        if base_url is None:
            raise NetworkNotSupportedError(network, provider="Toncenter")
        headers = {**(headers or {}), **({"X-Api-Key": api_key} if api_key else {})}

        super().__init__(
            base_url=base_url,
            session=session,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )

    async def send_boc(self, payload: SendBocPayload) -> None:
        """Send a BoC to the network.

        :param payload: Serialized BoC payload.
        """
        await self.send_http_request(
            "POST",
            "/sendBoc",
            json_data=asdict(payload),
        )

    async def get_config_all(self) -> GetConfigAllResult:
        """Fetch full blockchain configuration.

        :return: Parsed ``GetConfigAllResult``.
        """
        return self._model(
            GetConfigAllResult,
            await self.send_http_request("GET", "/getConfigAll"),
        )

    async def get_address_information(self, address: str) -> GetAddressInformationResult:
        """Fetch contract state information.

        :param address: Contract address string.
        :return: Parsed ``GetAddressInformationResult``.
        """
        return self._model(
            GetAddressInformationResult,
            await self.send_http_request(
                "GET",
                "/getAddressInformation",
                params={"address": address},
            ),
        )

    async def get_transactions(
        self,
        address: str,
        limit: int = 100,
        lt: int | None = None,
        from_hash: str | None = None,
        to_lt: int | None = None,
    ) -> GetTransactionsResult:
        """Fetch account transactions.

        :param address: Account address string.
        :param limit: Maximum transactions to return.
        :param lt: Starting logical time (requires ``from_hash``).
        :param from_hash: Starting transaction hash (requires ``lt``).
        :param to_lt: Lower-bound logical time filter.
        :return: Parsed ``GetTransactionsResult``.
        """
        params = {"address": address, "limit": limit, "archival": "true"}

        if lt is not None and from_hash is not None:
            params["lt"] = lt
            params["hash"] = from_hash

        if to_lt is not None:
            params["to_lt"] = to_lt

        return self._model(
            GetTransactionsResult,
            await self.send_http_request("GET", "/getTransactions", params=params),
        )

    async def run_get_method(self, payload: RunGetMethodPayload) -> RunGetMethodResult:
        """Execute a contract get-method.

        :param payload: Get-method request payload.
        :return: Parsed ``RunGetMethodResult``.
        """
        return self._model(
            RunGetMethodResult,
            await self.send_http_request(
                "POST",
                "/runGetMethod",
                json_data=asdict(payload),
            ),
        )
