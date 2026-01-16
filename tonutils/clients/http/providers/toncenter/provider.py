import typing as t

import aiohttp
from pydantic import BaseModel

from tonutils.clients.http.providers.base import HttpProvider
from tonutils.clients.http.providers.toncenter.models import (
    GetAddressInformationResult,
    GetConfigAllResult,
    GetTransactionResult,
    RunGetMethodResul,
    SendBocPayload,
    RunGetMethodPayload,
)
from tonutils.types import NetworkGlobalID, RetryPolicy


class ToncenterHttpProvider(HttpProvider):

    def __init__(
        self,
        network: NetworkGlobalID,
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

    @staticmethod
    def _model(model: t.Type[BaseModel], data: t.Any) -> t.Any:
        return model.model_validate(data)

    async def send_boc(
        self,
        payload: SendBocPayload,
    ) -> None:
        await self.send_http_request(
            "POST",
            "/sendBoc",
            json_data=payload.model_dump(),
        )

    async def get_config_all(
        self,
    ) -> GetConfigAllResult:
        return self._model(
            GetConfigAllResult,
            await self.send_http_request(
                "GET",
                "/getConfigAll",
            ),
        )

    async def get_address_information(
        self,
        address: str,
    ) -> GetAddressInformationResult:
        return self._model(
            GetAddressInformationResult,
            await self.send_http_request(
                "GET",
                "/getAddressInformation",
                params={"address": address},
            ),
        )

    async def get_transaction(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> GetTransactionResult:
        params = {"address": address, "limit": limit, "to_lt": to_lt}
        if from_lt is not None:
            params["from_lt"] = from_lt

        return self._model(
            GetTransactionResult,
            await self.send_http_request(
                "GET",
                "/getTransactions",
                params=params,
            ),
        )

    async def run_get_method(
        self,
        payload: RunGetMethodPayload,
    ) -> RunGetMethodResul:
        return self._model(
            RunGetMethodResul,
            await self.send_http_request(
                "POST",
                "/runGetMethod",
                json_data=payload.model_dump(),
            ),
        )
