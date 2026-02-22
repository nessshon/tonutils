import typing as t

import aiohttp

from tonutils.clients.http.provider.base import HttpProvider
from tonutils.clients.http.provider.models import (
    SendBocPayload,
    GetConfigAllResult,
    GetAddressInformationResult,
    GetTransactionsResult,
    RunGetMethodPayload,
    RunGetMethodResult,
)
from tonutils.types import NetworkGlobalID, RetryPolicy


class ToncenterHttpProvider(HttpProvider):
    """HTTP provider for the Toncenter API."""

    def __init__(
        self,
        network: NetworkGlobalID,
        *,
        api_key: t.Optional[str] = None,
        base_url: t.Optional[str] = None,
        timeout: float = 10.0,
        session: t.Optional[aiohttp.ClientSession] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        cookies: t.Optional[t.Dict[str, str]] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> None:
        """
        :param network: Target TON network.
        :param api_key: Toncenter API key, or `None`.
        :param base_url: Custom endpoint base URL, or `None`.
        :param timeout: Request timeout in seconds.
        :param session: External aiohttp session, or `None`.
        :param headers: Default headers for owned session.
        :param cookies: Default cookies for owned session.
        :param rps_limit: Requests-per-period limit, or `None`.
        :param rps_period: Rate limit period in seconds.
        :param retry_policy: Retry policy with per-error-code rules, or `None`.
        """
        urls = {
            NetworkGlobalID.MAINNET: "https://toncenter.com/api/v2",
            NetworkGlobalID.TESTNET: "https://testnet.toncenter.com/api/v2",
        }
        base_url = base_url or urls[network]
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
            json_data=payload.model_dump(),
        )

    async def get_config_all(self) -> GetConfigAllResult:
        """Fetch full blockchain configuration.

        :return: Parsed `GetConfigAllResult`.
        """
        return self._model(
            GetConfigAllResult,
            await self.send_http_request("GET", "/getConfigAll"),
        )

    async def get_address_information(
        self, address: str
    ) -> GetAddressInformationResult:
        """Fetch contract state information.

        :param address: Contract address string.
        :return: Parsed `GetAddressInformationResult`.
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
        lt: t.Optional[int] = None,
        from_hash: t.Optional[str] = None,
        to_lt: t.Optional[int] = None,
    ) -> GetTransactionsResult:
        """Fetch account transactions.

        :param address: Account address string.
        :param limit: Maximum transactions to return.
        :param lt: Starting logical time (requires `from_hash`).
        :param from_hash: Starting transaction hash (requires `lt`).
        :param to_lt: Lower-bound logical time filter.
        :return: Parsed `GetTransactionsResult`.
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
        :return: Parsed `RunGetMethodResult`.
        """
        return self._model(
            RunGetMethodResult,
            await self.send_http_request(
                "POST",
                "/runGetMethod",
                json_data=payload.model_dump(),
            ),
        )
