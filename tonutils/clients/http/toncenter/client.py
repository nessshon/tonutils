from __future__ import annotations

import base64
import typing as t

from aiohttp import ClientSession
from pytoniq_core import Cell, Slice, Transaction

from tonutils.clients.base import BaseClient
from tonutils.clients.http.toncenter.models import SendBocPayload, RunGetMethodPayload
from tonutils.clients.http.toncenter.provider import ToncenterHttpProvider
from tonutils.clients.http.toncenter.stack import decode_stack, encode_stack
from tonutils.exceptions import ClientError, ClientNotConnectedError
from tonutils.types import ClientType, ContractState, ContractStateInfo, NetworkGlobalID
from tonutils.utils import cell_to_hex, parse_stack_config


class ToncenterHttpClient(BaseClient):
    TYPE = ClientType.HTTP

    def __init__(
        self,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        api_key: t.Optional[str] = None,
        base_url: t.Optional[str] = None,
        timeout: int = 10,
        session: t.Optional[ClientSession] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
    ) -> None:
        self.network: NetworkGlobalID = network
        self._provider: ToncenterHttpProvider = ToncenterHttpProvider(
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
    def provider(self) -> ToncenterHttpProvider:
        if not self.is_connected:
            raise ClientNotConnectedError(self)
        return self._provider

    @property
    def is_connected(self) -> bool:
        session = self._provider.session
        return session is not None and not session.closed

    async def __aenter__(self) -> ToncenterHttpClient:
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
        payload = SendBocPayload(boc=boc)
        return await self.provider.send_boc(payload=payload)

    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        request = await self.provider.get_config_all()

        if request.result is None:
            raise ClientError(
                "Invalid get_config_all response: missing 'result' field."
            )

        if request.result.config is None:
            raise ClientError(
                "Invalid config response: missing 'config' section in result."
            )

        if request.result.config.bytes is None:
            raise ClientError(
                "Invalid config response: missing 'bytes' field in 'config' section."
            )

        config_cell = Cell.one_from_boc(request.result.config.bytes)
        config_slice = config_cell.begin_parse()
        return parse_stack_config(config_slice)

    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        request = await self.provider.get_address_information(address)

        contract_info = ContractStateInfo(
            balance=int(request.result.balance),
            state=ContractState(request.result.state),
        )
        if bool(request.result.code):
            contract_info.code_raw = cell_to_hex(request.result.code)

        if bool(request.result.data):
            contract_info.data_raw = cell_to_hex(request.result.data)

        last_transaction_lt = last_transaction_hash = None

        if request.result.last_transaction_id:
            try:
                lt = int(request.result.last_transaction_id.lt)
                last_transaction_lt = lt if lt > 0 else None
            except (TypeError, ValueError):
                last_transaction_lt = None
            try:
                raw = request.result.last_transaction_id.hash
                decoded = base64.b64decode(raw)
                h = decoded.hex()
                last_transaction_hash = None if h == "00" * 32 else h
            except (Exception,):
                last_transaction_hash = None

        contract_info.last_transaction_lt = last_transaction_lt
        contract_info.last_transaction_hash = last_transaction_hash

        if (
            last_transaction_lt is None
            and last_transaction_hash is None
            and contract_info.state == ContractState.UNINIT
        ):
            contract_info.state = ContractState.NONEXIST

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

        request = await self.provider.get_transaction(
            address=address,
            limit=limit,
            from_lt=from_lt,
            to_lt=to_lt,
        )

        transactions = []
        for tx in request.result or []:
            if tx.data is not None:
                tx_slice = Slice.one_from_boc(tx.data)
                transactions.append(Transaction.deserialize(tx_slice))

        return transactions

    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        payload = RunGetMethodPayload(
            address=address,
            method=method_name,
            stack=encode_stack(stack or []),
        )
        request = await self.provider.run_get_method(payload=payload)
        if request.result is None:
            return []
        return decode_stack(request.result.stack or [])

    async def connect(self) -> None:
        await self._provider.ensure_session()

    async def close(self) -> None:
        await self._provider.close()
