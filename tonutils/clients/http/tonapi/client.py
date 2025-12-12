from __future__ import annotations

import typing as t

from aiohttp import ClientSession
from pytoniq_core import Cell, Slice, Transaction

from tonutils.clients.base import BaseClient
from tonutils.clients.http.tonapi.models import BlockchainMessagePayload
from tonutils.clients.http.tonapi.provider import TonapiHttpProvider
from tonutils.clients.http.tonapi.stack import decode_stack, encode_stack
from tonutils.exceptions import ClientError, ClientNotConnectedError
from tonutils.types import (
    ClientType,
    ContractState,
    ContractStateInfo,
    NetworkGlobalID,
)
from tonutils.utils import (
    cell_to_hex,
    parse_stack_config,
)


class TonapiHttpClient(BaseClient):
    """TON blockchain client using Tonapi HTTP API as transport."""

    TYPE = ClientType.HTTP

    def __init__(
        self,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        api_key: str,
        base_url: t.Optional[str] = None,
        timeout: int = 10,
        session: t.Optional[ClientSession] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
    ) -> None:
        """
        Initialize Tonapi HTTP client.

        :param network: Target TON network (mainnet or testnet)
        :param api_key: Tonapi API key
            You can get an API key on the Tonconsole website: https://tonconsole.com/
        :param base_url: Optional custom Tonapi base URL
        :param timeout: HTTP request timeout in seconds
        :param session: Optional externally managed aiohttp.ClientSession
        :param rps_limit: Optional requests-per-second limit
        :param rps_period: Time window in seconds for rate limiting
        :param rps_retries: Number of retries on rate limiting
        """
        self.network: NetworkGlobalID = network
        self._provider: TonapiHttpProvider = TonapiHttpProvider(
            api_key=api_key,
            network=network,
            base_url=base_url,
            timeout=timeout,
            session=session,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
        )

    @property
    def provider(self) -> TonapiHttpProvider:
        """
        Underlying Tonapi HTTP provider.

        :return: TonapiHttpProvider instance used for HTTP requests
        """
        if not self.is_connected:
            raise ClientNotConnectedError(self)
        return self._provider

    @property
    def is_connected(self) -> bool:
        """
        Check whether HTTP session is initialized and open.

        :return: True if session exists and is not closed, False otherwise
        """
        session = self._provider.session
        return session is not None and not session.closed

    async def __aenter__(self) -> TonapiHttpClient:
        await self._provider.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        await self._provider.__aexit__(exc_type, exc_value, traceback)

    async def _send_boc(self, boc: str) -> None:
        payload = BlockchainMessagePayload(boc=boc)
        return await self.provider.blockchain_message(payload=payload)

    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        result = await self.provider.blockchain_config()

        if result.raw is None:
            raise ClientError("Invalid config response: missing `raw` field.")

        config_cell = Cell.one_from_boc(result.raw)[0]
        config_slice = config_cell.begin_parse()
        return parse_stack_config(config_slice)

    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        result = await self.provider.blockchain_account(address)

        contract_info = ContractStateInfo(
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

    async def _get_contract_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]:
        if from_lt is not None:
            from_lt += 1

        result = await self.provider.blockchain_account_transactions(
            address=address,
            limit=limit,
            after_lt=to_lt,
            before_lt=from_lt,
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
            args=encode_stack(stack or []),
        )
        return decode_stack(result.stack or [])

    async def connect(self) -> None:
        """Ensure that HTTP session is initialized."""
        await self._provider.ensure_session()

    async def close(self) -> None:
        """Close HTTP session if it is owned by the provider."""
        await self._provider.close()
