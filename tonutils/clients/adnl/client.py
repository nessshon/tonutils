from __future__ import annotations

import typing as t

from pytoniq_core import Address, Transaction

from tonutils.clients.adnl.provider import AdnlProvider
from tonutils.clients.adnl.provider.limiter import PriorityLimiter
from tonutils.clients.adnl.provider.models import LiteServer
from tonutils.clients.adnl.stack import decode_stack, encode_stack
from tonutils.clients.base import BaseClient
from tonutils.types import BinaryLike, ClientType, ContractStateInfo, NetworkGlobalID


class AdnlClient(BaseClient):
    TYPE = ClientType.ADNL

    def __init__(
        self,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        ip: t.Union[str, int],
        port: int,
        public_key: BinaryLike,
        timeout: int = 10,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
        limiter: t.Optional[PriorityLimiter] = None,
    ) -> None:
        self.network: NetworkGlobalID = network

        if limiter is not None:
            limiter = limiter
        elif rps_limit is not None:
            limiter = PriorityLimiter(rps_limit, rps_period)

        self._provider: AdnlProvider = AdnlProvider(
            node=LiteServer(
                ip=ip,
                port=port,
                id=public_key,
            ),
            timeout=timeout,
            rps_retries=rps_retries,
            limiter=limiter,
        )

    @property
    def provider(self) -> AdnlProvider:
        return self._provider

    @property
    def is_connected(self) -> bool:
        return self._provider.is_connected

    async def __aenter__(self) -> AdnlClient:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        await self.close()

    async def _send_boc(self, boc: str) -> None:
        return await self.provider.send_message(bytes.fromhex(boc))

    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        return await self.provider.get_config_all()

    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        return await self.provider.get_account_state(Address(address))

    async def _get_contract_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]:
        state = await self._get_contract_info(address)
        account = Address(address).to_tl_account_id()

        if state.last_transaction_lt is None or state.last_transaction_hash is None:
            return []

        curr_lt = state.last_transaction_lt
        curr_hash = state.last_transaction_hash
        transactions: list[Transaction] = []

        while len(transactions) < limit and curr_lt != 0:
            batch_size = min(16, limit - len(transactions))

            txs = await self.provider.get_transactions(
                account=account,
                count=batch_size,
                from_lt=curr_lt,
                from_hash=curr_hash,
            )
            if not txs:
                break

            if to_lt > 0 and txs[-1].lt <= to_lt:
                trimmed: list[Transaction] = []
                for tx in txs:
                    if tx.lt <= to_lt:
                        break
                    trimmed.append(tx)
                transactions.extend(trimmed)
                break

            transactions.extend(txs)

            last_tx = txs[-1]
            curr_lt = last_tx.prev_trans_lt
            curr_hash = last_tx.prev_trans_hash.hex()

        return (
            [tx for tx in transactions if tx.lt < from_lt]
            if from_lt is not None
            else transactions
        )

    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        result = await self.provider.run_smc_method(
            address=Address(address),
            method_name=method_name,
            stack=encode_stack(stack or []),
        )
        return decode_stack(result or [])

    async def connect(self) -> None:
        await self.provider.connect()

    async def reconnect(self) -> None:
        await self.provider.reconnect()

    async def close(self) -> None:
        await self.provider.close()
