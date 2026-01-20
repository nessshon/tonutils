from __future__ import annotations

import base64
import typing as t

from aiohttp import ClientSession
from pytoniq_core import Cell, Slice, Transaction

from tonutils.clients.base import BaseClient
from tonutils.clients.http.provider.models import SendBocPayload, RunGetMethodPayload
from tonutils.clients.http.provider.toncenter import ToncenterHttpProvider
from tonutils.clients.http.utils import decode_toncenter_stack, encode_toncenter_stack
from tonutils.exceptions import ClientError, RunGetMethodError
from tonutils.types import (
    ClientType,
    ContractState,
    ContractStateInfo,
    NetworkGlobalID,
    RetryPolicy,
)
from tonutils.utils import cell_to_hex, parse_stack_config


class ToncenterClient(BaseClient):
    """TON blockchain client using Toncenter HTTP API as transport."""

    TYPE = ClientType.HTTP

    def __init__(
        self,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        api_key: t.Optional[str] = None,
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
        Initialize Toncenter HTTP client.

        :param network: Target TON network (mainnet or testnet)
        :param api_key: Optional Toncenter API key
            You can get an API key on the Toncenter telegram bot: https://t.me/toncenter
        :param base_url: Custom Toncenter endpoint base URL
        :param timeout: Total request timeout in seconds.
        :param session: Optional external aiohttp session.
        :param headers: Default headers for owned session.
        :param cookies: Default cookies for owned session.
        :param rps_limit: Optional requests-per-period limit.
        :param rps_period: Rate limit period in seconds.
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        """
        self.network: NetworkGlobalID = network
        self._provider: ToncenterHttpProvider = ToncenterHttpProvider(
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
    def provider(self) -> ToncenterHttpProvider:
        return self._provider

    @property
    def is_connected(self) -> bool:
        session = self._provider.session
        return session is not None and not session.closed

    async def __aenter__(self) -> ToncenterClient:
        await self._provider.connect()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        await self._provider.close()

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

        tx_id = request.result.last_transaction_id
        if tx_id is not None:
            try:
                lt = int(tx_id.lt) if tx_id.lt is not None else 0
            except (ValueError,):
                pass
            else:
                if lt > 0:
                    last_transaction_lt = lt

            raw = tx_id.hash
            if raw is not None:
                try:
                    h = base64.b64decode(raw).hex()
                except (Exception,):
                    pass
                else:
                    if h != "00" * 32:
                        last_transaction_hash = h

        contract_info.last_transaction_lt = last_transaction_lt
        contract_info.last_transaction_hash = last_transaction_hash

        if (
            last_transaction_lt is None
            and last_transaction_hash is None
            and contract_info.state == ContractState.UNINIT
        ):
            contract_info.state = ContractState.NONEXIST

        return contract_info

    async def _get_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = None,
    ) -> t.List[Transaction]:
        to_lt = 0 if to_lt is None else to_lt
        transactions: t.List[Transaction] = []

        curr_lt: t.Optional[int] = None
        curr_hash: t.Optional[str] = None

        while len(transactions) < limit:
            request = await self.provider.get_transactions(
                address=address,
                limit=100,
                lt=curr_lt,
                from_hash=curr_hash,
                to_lt=to_lt if to_lt > 0 else None,
            )

            batch = []
            for tx in request.result or []:
                if tx.data is not None:
                    tx_slice = Slice.one_from_boc(tx.data)
                    batch.append(Transaction.deserialize(tx_slice))

            if not batch:
                break

            for tx in batch:
                # Skip transactions above from_lt (if specified)
                if from_lt is not None and tx.lt > from_lt:
                    continue

                # Stop if we've reached the lower bound
                if to_lt > 0 and tx.lt <= to_lt:
                    return transactions[:limit]

                transactions.append(tx)

                if len(transactions) >= limit:
                    return transactions

            # Setup for next iteration
            last_tx = batch[-1]
            if last_tx.prev_trans_lt == 0:
                break

            curr_lt = last_tx.prev_trans_lt
            curr_hash = last_tx.prev_trans_hash.hex()

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
            stack=encode_toncenter_stack(stack or []),
        )
        request = await self.provider.run_get_method(payload=payload)
        if request.result is None:
            return []

        if request.result.exit_code != 0:
            raise RunGetMethodError(
                address=address,
                method_name=method_name,
                exit_code=request.result.exit_code,
            )

        return decode_toncenter_stack(request.result.stack or [])

    async def connect(self) -> None:
        await self._provider.connect()

    async def close(self) -> None:
        await self._provider.close()
