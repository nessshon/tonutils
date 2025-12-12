import typing as t

from aiohttp import ClientSession
from pyapiq import AsyncClientAPI, async_endpoint
from pyapiq.types import HTTPMethod, ReturnType, RepeatQuery

from tonutils.clients.http.tonapi.models import (
    BlockchainAccountMethodResult,
    BlockchainAccountResult,
    BlockchainAccountTransactionsResult,
    BlockchainConfigResult,
    BlockchainMessagePayload,
)
from tonutils.types import NetworkGlobalID


class TonapiHttpProvider(AsyncClientAPI):
    """Low-level HTTP provider for Tonapi API."""

    version = "v2"

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
        Initialize provider with Tonapi API settings.

        :param network: TON network selector (mainnet/testnet)
        :param api_key: Tonapi API key
            You can get an API key on the Tonconsole website: https://tonconsole.com/
        :param base_url: Custom Tonapi base URL
        :param timeout: HTTP request timeout in seconds
        :param session: Optional aiohttp.ClientSession, external or auto-created
        :param rps_limit: Requests-per-second rate limit
        :param rps_period: Time period window for rate limiting
        :param rps_retries: Number of retries on rate-limit errors
        """
        urls = {
            NetworkGlobalID.MAINNET: "https://tonapi.io",
            NetworkGlobalID.TESTNET: "https://testnet.tonapi.io",
        }
        base_url = base_url or urls.get(network)
        headers = {"Authorization": f"Bearer {api_key}"}

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
        path="/blockchain/message",
        return_as=ReturnType.NONE,
    )
    async def blockchain_message(  # type: ignore[empty-body]
        self,
        payload: BlockchainMessagePayload,
    ) -> None:
        """
        Send an external message to the blockchain.

        :param payload: Payload with base64-encoded BoC
        """

    @async_endpoint(
        HTTPMethod.GET,
        path="/blockchain/config",
        return_as=BlockchainConfigResult,
    )
    async def blockchain_config(  # type: ignore[empty-body]
        self,
    ) -> BlockchainConfigResult:
        """
        Fetch global blockchain configuration.

        :return: BlockchainConfigResult with raw config BoC
        """

    @async_endpoint(
        HTTPMethod.GET,
        path="/blockchain/accounts/{address}",
        return_as=BlockchainAccountResult,
    )
    async def blockchain_account(  # type: ignore[empty-body]
        self,
        address: str,
    ) -> BlockchainAccountResult:
        """
        Fetch basic account information.

        :param address: Raw TON address
        :return: BlockchainAccountResult
        """

    @async_endpoint(
        HTTPMethod.GET,
        path="/blockchain/accounts/{address}/transactions",
        return_as=BlockchainAccountTransactionsResult,
    )
    async def blockchain_account_transactions(  # type: ignore[empty-body]
        self,
        address: str,
        limit: int = 100,
        after_lt: t.Optional[int] = None,
        before_lt: t.Optional[int] = 0,
        sort_order: t.Optional[t.Literal["asc", "desc"]] = "desc",
    ) -> BlockchainAccountTransactionsResult:
        """
        Fetch recent transactions for an account.

        :param address: Raw TON address
        :param limit: Maximum number of transactions to return
        :param after_lt: Lower logical-time bound (exclusive)
        :param before_lt: Upper logical-time bound (inclusive)
        :param sort_order: Transaction sorting order ("asc" or "desc")
        :return: BlockchainAccountTransactionsResult
        """

    @async_endpoint(
        HTTPMethod.GET,
        path="/blockchain/accounts/{address}/methods/{method_name}",
        return_as=BlockchainAccountMethodResult,
    )
    async def blockchain_account_method(  # type: ignore[empty-body]
        self,
        address: str,
        method_name: str,
        args: t.Annotated[t.List[t.Any], RepeatQuery],
    ) -> BlockchainAccountMethodResult:
        """
        Execute a smart-contract get-method via Tonapi.

        :param address: Raw TON address
        :param method_name: Name of the method to execute
        :param args: Encoded TVM stack arguments (repeatable query items)
        :return: BlockchainAccountMethodResult with stack output
        """
