import typing as t

from pyapiq import AsyncClientAPI, async_endpoint
from pyapiq.types import ReturnType, HTTPMethod

from .models import (
    SendBocPayload,
    GetConfigAllResult,
    GetAddressInformationResult,
    GetTransactionResult,
    RunGetMethodResul,
    RunGetMethodPayload,
)


class ToncenterAPI(AsyncClientAPI):
    version = "v2"

    def __init__(
        self,
        api_key: t.Optional[str] = None,
        is_testnet: bool = False,
        base_url: t.Optional[str] = None,
        rps: t.Optional[int] = None,
        max_retries: t.Optional[int] = None,
    ) -> None:
        mainnet_url = "https://toncenter.com/api"
        testnet_url = "https://testnet.toncenter.com/api"
        default_url = testnet_url if is_testnet else mainnet_url

        base_url = base_url or default_url
        headers = {"X-Api-Key": api_key} if api_key else {}

        super().__init__(
            base_url=base_url,
            headers=headers,
            rps=rps,
            max_retries=max_retries,
        )

    @async_endpoint(
        HTTPMethod.POST,
        path="/sendBoc",
        return_as=ReturnType.NONE,
    )
    async def send_boc(  # type: ignore[empty-body]
        self,
        payload: SendBocPayload,
    ) -> None: ...

    @async_endpoint(
        HTTPMethod.GET,
        path="/getConfigAll",
        return_as=GetConfigAllResult,
    )
    async def get_config_all(  # type: ignore[empty-body]
        self,
    ) -> GetConfigAllResult: ...

    @async_endpoint(
        HTTPMethod.GET,
        path="/getAddressInformation",
        return_as=GetAddressInformationResult,
    )
    async def get_address_information(  # type: ignore[empty-body]
        self,
        address: str,
    ) -> GetAddressInformationResult: ...

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
        to_lt: t.Optional[int] = 0,
    ) -> GetTransactionResult: ...

    @async_endpoint(
        HTTPMethod.POST,
        path="/runGetMethod",
        return_as=RunGetMethodResul,
    )
    async def run_get_method(  # type: ignore[empty-body]
        self,
        payload: RunGetMethodPayload,
    ) -> RunGetMethodResul: ...
