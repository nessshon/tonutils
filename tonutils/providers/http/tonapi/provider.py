from __future__ import annotations

import typing as t
from dataclasses import asdict

from ton_core import NetworkGlobalID

from tonutils.exceptions import NetworkNotSupportedError
from tonutils.providers.http.tonapi.models import (
    BlockchainAccountMethodResult,
    BlockchainAccountResult,
    BlockchainAccountTransactionsResult,
    BlockchainConfigResult,
    BlockchainMessagePayload,
    GaslessConfigResult,
    GaslessEstimatePayload,
    GaslessEstimateResult,
    GaslessSendPayload,
)
from tonutils.transports.http import HttpTransport
from tonutils.types import DEFAULT_REQUEST_TIMEOUT

if t.TYPE_CHECKING:
    import aiohttp

    from tonutils.types import RetryPolicy


class TonapiHttpProvider(HttpTransport):
    """HTTP provider for the Tonapi API."""

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
        """Initialize the Tonapi HTTP provider.

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
            NetworkGlobalID.MAINNET: "https://tonapi.io/v2",
            NetworkGlobalID.TESTNET: "https://testnet.tonapi.io/v2",
            NetworkGlobalID.TETRA: "https://tetra.tonapi.io/v2",
        }
        base_url = base_url or urls.get(network)
        if base_url is None:
            raise NetworkNotSupportedError(network, provider="Tonapi")
        headers = {**(headers or {}), **({"Authorization": f"Bearer {api_key}"} if api_key else {})}

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

    async def blockchain_message(self, payload: BlockchainMessagePayload) -> None:
        """Send an external message to the blockchain.

        :param payload: Message payload with BoC.
        """
        await self.send_http_request(
            "POST",
            "/blockchain/message",
            json_data=asdict(payload),
        )

    async def blockchain_config(self) -> BlockchainConfigResult:
        """Fetch blockchain configuration.

        :return: Parsed ``BlockchainConfigResult``.
        """
        return self._model(
            BlockchainConfigResult,
            await self.send_http_request("GET", "/blockchain/config"),
        )

    async def blockchain_account(self, address: str) -> BlockchainAccountResult:
        """Fetch account information.

        :param address: Account address string.
        :return: Parsed ``BlockchainAccountResult``.
        """
        return self._model(
            BlockchainAccountResult,
            await self.send_http_request("GET", f"/blockchain/accounts/{address}"),
        )

    async def blockchain_account_transactions(
        self,
        address: str,
        limit: int = 100,
        after_lt: int | None = None,
        before_lt: int | None = None,
    ) -> BlockchainAccountTransactionsResult:
        """Fetch account transactions.

        :param address: Account address string.
        :param limit: Maximum transactions to return.
        :param after_lt: Lower-bound logical time filter.
        :param before_lt: Upper-bound logical time filter.
        :return: Parsed ``BlockchainAccountTransactionsResult``.
        """
        params = {"limit": limit}
        if after_lt is not None:
            params["after_lt"] = after_lt
        if before_lt is not None:
            params["before_lt"] = before_lt

        return self._model(
            BlockchainAccountTransactionsResult,
            await self.send_http_request(
                "GET",
                f"/blockchain/accounts/{address}/transactions",
                params=params,
            ),
        )

    async def blockchain_account_method(
        self,
        address: str,
        method_name: str,
        args: list[t.Any],
    ) -> BlockchainAccountMethodResult:
        """Execute a contract get-method.

        :param address: Contract address string.
        :param method_name: Name of the get-method.
        :param args: Encoded TVM stack arguments.
        :return: Parsed ``BlockchainAccountMethodResult``.
        """
        return self._model(
            BlockchainAccountMethodResult,
            await self.send_http_request(
                "POST",
                f"/blockchain/accounts/{address}/methods/{method_name}",
                json_data={"args": args or []},
            ),
        )

    async def gasless_config(self) -> GaslessConfigResult:
        """Fetch gasless transfer configuration.

        :return: Parsed ``GaslessConfigResult`` with relay address and supported jettons.
        """
        return self._model(
            GaslessConfigResult,
            await self.send_http_request("GET", "/gasless/config"),
        )

    async def gasless_estimate(
        self,
        master_id: str,
        payload: GaslessEstimatePayload,
    ) -> GaslessEstimateResult:
        """Estimate gasless transfer fees.

        :param master_id: Jetton master address string.
        :param payload: Estimation request payload.
        :return: Parsed ``GaslessEstimateResult`` with messages to sign.
        """
        return self._model(
            GaslessEstimateResult,
            await self.send_http_request(
                "POST",
                f"/gasless/estimate/{master_id}",
                json_data=asdict(payload),
            ),
        )

    async def gasless_send(self, payload: GaslessSendPayload) -> None:
        """Send a signed gasless transfer.

        :param payload: Signed message payload.
        """
        await self.send_http_request(
            "POST",
            "/gasless/send",
            json_data=asdict(payload),
        )
