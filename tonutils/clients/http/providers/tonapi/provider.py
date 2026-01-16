from __future__ import annotations

import typing as t

import aiohttp
from pydantic import BaseModel

from tonutils.clients.http.providers.base import HttpProvider
from tonutils.clients.http.providers.tonapi.models import (
    BlockchainAccountMethodResult,
    BlockchainAccountResult,
    BlockchainAccountTransactionsResult,
    BlockchainConfigResult,
    BlockchainMessagePayload,
)
from tonutils.types import NetworkGlobalID, RetryPolicy


class TonapiHttpProvider(HttpProvider):

    def __init__(
        self,
        network: NetworkGlobalID,
        api_key: str,
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
            NetworkGlobalID.MAINNET: "https://tonapi.io/v2",
            NetworkGlobalID.TESTNET: "https://testnet.tonapi.io/v2",
        }
        base_url = base_url or urls[network]
        headers = {**(headers or {}), "Authorization": f"Bearer {api_key}"}

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

    async def blockchain_message(
        self,
        payload: BlockchainMessagePayload,
    ) -> None:
        await self.send_http_request(
            "POST",
            "/blockchain/message",
            json_data=payload.model_dump(),
        )

    async def blockchain_config(
        self,
    ) -> BlockchainConfigResult:
        return self._model(
            BlockchainConfigResult,
            await self.send_http_request(
                "GET",
                "/blockchain/config",
            ),
        )

    async def blockchain_account(
        self,
        address: str,
    ) -> BlockchainAccountResult:
        return self._model(
            BlockchainAccountResult,
            await self.send_http_request(
                "GET",
                f"/blockchain/accounts/{address}",
            ),
        )

    async def blockchain_account_transactions(
        self,
        address: str,
        limit: int = 100,
        after_lt: t.Optional[int] = None,
        before_lt: t.Optional[int] = None,
        sort_order: str = "desc",
    ) -> BlockchainAccountTransactionsResult:
        params = {"limit": limit, "sort_order": sort_order}
        if after_lt is not None:
            params["after_lt"] = after_lt
        if before_lt is not None and before_lt > 0:
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
        args: t.List[t.Any],
    ) -> BlockchainAccountMethodResult:
        return self._model(
            BlockchainAccountMethodResult,
            await self.send_http_request(
                "GET",
                f"/blockchain/accounts/{address}/methods/{method_name}",
                params={"args": args} if args else None,
            ),
        )
