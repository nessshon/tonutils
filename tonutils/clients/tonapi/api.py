import typing as t

from pyapiq import AsyncClientAPI, async_endpoint
from pyapiq.types import ReturnType, RepeatQuery, HTTPMethod

from .models import (
    BlockchainMessagePayload,
    BlockchainConfigResult,
    BlockchainAccountResult,
    BlockchainAccountTransactionsResult,
    BlockchainAccountMethodResult,
)


class TonapiAPI(AsyncClientAPI):
    version = "v2"

    def __init__(
        self,
        api_key: str,
        is_testnet: bool = False,
        base_url: t.Optional[str] = None,
        rps: t.Optional[int] = None,
        max_retries: t.Optional[int] = None,
    ) -> None:
        mainnet_url = "https://tonapi.io"
        testnet_url = "https://testnet.tonapi.io"
        default_url = testnet_url if is_testnet else mainnet_url

        base_url = base_url or default_url
        headers = {"Authorization": f"Bearer {api_key}"}

        super().__init__(
            base_url=base_url,
            headers=headers,
            rps=rps,
            max_retries=max_retries,
        )

    @async_endpoint(
        HTTPMethod.POST,
        path="/blockchain/message",
        return_as=ReturnType.NONE,
    )
    async def blockchain_message(  # type: ignore[empty-body]
        self,
        payload: BlockchainMessagePayload,
    ) -> None: ...

    @async_endpoint(
        HTTPMethod.GET,
        path="/blockchain/config",
        return_as=BlockchainConfigResult,
    )
    async def blockchain_config(  # type: ignore[empty-body]
        self,
    ) -> BlockchainConfigResult: ...

    @async_endpoint(
        HTTPMethod.GET,
        path="/blockchain/accounts/{address}",
        return_as=BlockchainAccountResult,
    )
    async def blockchain_account(  # type: ignore[empty-body]
        self,
        address: str,
    ) -> BlockchainAccountResult: ...

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
    ) -> BlockchainAccountTransactionsResult: ...

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
    ) -> BlockchainAccountMethodResult: ...
