import typing as t

from aiohttp import ClientSession
from pyapiq import AsyncClientAPI, async_endpoint
from pyapiq.types import ReturnType, HTTPMethod

from tonutils.clients.http.toncenter.models import (
    GetAddressInformationResult,
    GetConfigAllResult,
    GetTransactionResult,
    RunGetMethodPayload,
    RunGetMethodResul,
    SendBocPayload,
)
from tonutils.types import NetworkGlobalID


class ToncenterHttpProvider(AsyncClientAPI):
    """Low-level HTTP provider for Toncenter API."""

    version = "v2"

    def __init__(
        self,
        network: NetworkGlobalID,
        api_key: t.Optional[str] = None,
        base_url: t.Optional[str] = None,
        timeout: int = 10,
        session: t.Optional[ClientSession] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: t.Optional[float] = None,
        rps_retries: t.Optional[int] = None,
    ) -> None:
        """
        Initialize provider with Toncenter API settings.

        :param network: TON network selector (mainnet/testnet)
        :param api_key: Optional Toncenter API key
            You can get an API key on the Toncenter telegram bot: https://t.me/toncenter
        :param base_url: Custom Toncenter endpoint base URL
        :param timeout: HTTP request timeout in seconds
        :param session: Optional aiohttp.ClientSession, external or auto-created
        :param rps_limit: Requests-per-second rate limit
        :param rps_period: Time period window for rate limiting
        :param rps_retries: Number of retries on rate-limit errors
        """
        urls = {
            NetworkGlobalID.MAINNET: "https://toncenter.com/api",
            NetworkGlobalID.TESTNET: "https://testnet.toncenter.com/api",
        }
        base_url = base_url or urls.get(network)
        headers = {"X-Api-Key": api_key} if api_key else {}

        super().__init__(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            session=session,
            rps=rps_limit,
            time_period=rps_period,
            max_retries=rps_retries,
        )

    @async_endpoint(
        HTTPMethod.POST,
        path="/sendBoc",
        return_as=ReturnType.NONE,
    )
    async def send_boc(  # type: ignore[empty-body]
        self,
        payload: SendBocPayload,
    ) -> None:
        """
        Send an external message to the blockchain.

        :param payload: Pre-validated SendBocPayload with BoC data
        """

    @async_endpoint(
        HTTPMethod.GET,
        path="/getConfigAll",
        return_as=GetConfigAllResult,
    )
    async def get_config_all(  # type: ignore[empty-body]
        self,
    ) -> GetConfigAllResult:
        """
        Fetch the full blockchain configuration dictionary.

        :return: Parsed GetConfigAllResult object
        """

    @async_endpoint(
        HTTPMethod.GET,
        path="/getAddressInformation",
        return_as=GetAddressInformationResult,
    )
    async def get_address_information(  # type: ignore[empty-body]
        self,
        address: str,
    ) -> GetAddressInformationResult:
        """
        Fetch basic information about a contract.

        :param address: Raw TON address (workchain:hash)
        :return: GetAddressInformationResult
        """

    @async_endpoint(
        HTTPMethod.GET,
        path="/getTransactions",
        return_as=GetTransactionResult,
    )
    async def get_transaction(  # type: ignore[empty-body]
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> GetTransactionResult:
        """
        Fetch recent transactions for a contract.

        :param address: Raw TON address
        :param limit: Maximum number of transactions to return
        :param from_lt: Lower logical-time bound (exclusive)
        :param to_lt: Upper logical-time bound (inclusive)
        :return: GetTransactionResult
        """

    @async_endpoint(
        HTTPMethod.POST,
        path="/runGetMethod",
        return_as=RunGetMethodResul,
    )
    async def run_get_method(  # type: ignore[empty-body]
        self,
        payload: RunGetMethodPayload,
    ) -> RunGetMethodResul:
        """
        Execute a smart-contract get-method.

        :param payload: RunGetMethodPayload containing method name and stack
        :return: RunGetMethodResul with TVM stack output
        """
