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
        to_lt: int = 0,
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
