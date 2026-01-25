from __future__ import annotations

import typing as t

from aiohttp import ClientSession
from pytoniq_core import Cell, Slice, Transaction

from tonutils.clients.base import BaseClient
from tonutils.clients.http.provider.models import BlockchainMessagePayload
from tonutils.clients.http.provider.tonapi import TonapiHttpProvider
from tonutils.clients.http.utils import encode_tonapi_stack, decode_tonapi_stack
from tonutils.exceptions import ClientError, RunGetMethodError
from tonutils.types import (
    ClientType,
    ContractState,
    ContractInfo,
    NetworkGlobalID,
    RetryPolicy,
)
from tonutils.utils import (
    cell_to_hex,
    parse_stack_config,
)


class TonapiClient(BaseClient):
    """TON blockchain client using Tonapi HTTP API as transport."""

    TYPE = ClientType.HTTP

    def __init__(
        self,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        api_key: str,
        base_url: t.Optional[str] = None,
        timeout: float = 10.0,
        session: t.Optional[ClientSession] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        cookies: t.Optional[t.Dict[str, str]] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> None:
        """
        Initialize Tonapi HTTP client.

        :param network: Target TON network (mainnet or testnet)
        :param api_key: Tonapi API key
            You can get an API key on the Tonconsole website: https://tonconsole.com/
        :param base_url: Optional custom Tonapi base URL
        :param timeout: Total request timeout in seconds.
        :param session: Optional external aiohttp session.
        :param headers: Default headers for owned session.
        :param cookies: Default cookies for owned session.
        :param rps_limit: Optional requests-per-period limit.
        :param rps_period: Rate limit period in seconds.
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        """
        self.network: NetworkGlobalID = network
        self._provider: TonapiHttpProvider = TonapiHttpProvider(
            api_key=api_key,
            network=network,
            base_url=base_url,
            timeout=timeout,
            session=session,
            headers=headers,
            cookies=cookies,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )

    @property
    def connected(self) -> bool:
        session = self._provider.session
        return session is not None and not session.closed

    @property
    def provider(self) -> TonapiHttpProvider:
        return self._provider

    async def connect(self) -> None:
        await self._provider.connect()

    async def close(self) -> None:
        await self._provider.close()

    async def _send_message(self, boc: str) -> None:
        payload = BlockchainMessagePayload(boc=boc)
        return await self.provider.blockchain_message(payload=payload)

    async def _get_config(self) -> t.Dict[int, t.Any]:
        result = await self.provider.blockchain_config()

        if result.raw is None:
            raise ClientError("Invalid config response: missing `raw` field.")

        config_cell = Cell.one_from_boc(result.raw)[0]
        config_slice = config_cell.begin_parse()
        return parse_stack_config(config_slice)

    async def _get_info(self, address: str) -> ContractInfo:
        result = await self.provider.blockchain_account(address)

        contract_info = ContractInfo(
            balance=result.balance,
            state=ContractState(result.status),
            last_transaction_lt=result.last_transaction_lt,
            last_transaction_hash=result.last_transaction_hash,
        )
        if result.code is not None:
            contract_info.code_raw = cell_to_hex(result.code)
        if result.data is not None:
            contract_info.data_raw = cell_to_hex(result.data)

        return contract_info

    async def _get_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = None,
    ) -> t.List[Transaction]:
        before_lt = from_lt + 1 if from_lt is not None else None

        result = await self.provider.blockchain_account_transactions(
            address=address,
            limit=limit,
            after_lt=to_lt,
            before_lt=before_lt,
        )

        transactions = []
        for tx in result.transactions or []:
            if tx.raw is not None:
                tx_slice = Slice.one_from_boc(tx.raw)
                transactions.append(Transaction.deserialize(tx_slice))

        return transactions

    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        result = await self.provider.blockchain_account_method(
            address=address,
            method_name=method_name,
            args=encode_tonapi_stack(stack or []),
        )
        if result.exit_code != 0:
            raise RunGetMethodError(
                address=address,
                method_name=method_name,
                exit_code=result.exit_code,
            )

        return decode_tonapi_stack(result.stack or [])
