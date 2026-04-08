from __future__ import annotations

import pytest
from ton_core import Address, ContractState

from tests.constants import ELECTOR_ADDRESS, NONEXISTENT_ADDRESS, USDT_MASTER_ADDRESS
from tonutils.exceptions import RunGetMethodError


class TestGetInfo:
    async def test_active_contract(self, client):
        info = await client.get_info(ELECTOR_ADDRESS)
        assert info.state == ContractState.ACTIVE
        assert info.balance > 0
        assert info.last_transaction_lt is not None
        assert info.last_transaction_lt > 0

    async def test_has_code_and_data(self, client):
        info = await client.get_info(USDT_MASTER_ADDRESS)
        assert info.code_raw is not None
        assert info.data_raw is not None

    async def test_accepts_address_object(self, client):
        info = await client.get_info(Address(ELECTOR_ADDRESS))
        assert info.state == ContractState.ACTIVE

    async def test_nonexistent_contract(self, client):
        info = await client.get_info(NONEXISTENT_ADDRESS)
        assert info.state == ContractState.NONEXIST
        assert info.balance == 0
        assert info.code_raw is None
        assert info.data_raw is None


class TestGetTransactions:
    async def test_returns_ordered_by_lt(self, client):
        txs = await client.get_transactions(ELECTOR_ADDRESS, limit=5)
        assert len(txs) > 0
        lts = [tx.lt for tx in txs]
        assert lts == sorted(lts, reverse=True)

    async def test_limit_respected(self, client):
        txs = await client.get_transactions(ELECTOR_ADDRESS, limit=3)
        assert len(txs) <= 3

    async def test_from_lt_filters(self, client):
        all_txs = await client.get_transactions(ELECTOR_ADDRESS, limit=5)
        if len(all_txs) < 3:
            pytest.skip("Not enough transactions")
        mid_lt = all_txs[2].lt
        filtered = await client.get_transactions(ELECTOR_ADDRESS, limit=5, from_lt=mid_lt)
        for tx in filtered:
            assert tx.lt <= mid_lt

    async def test_to_lt_filters(self, client):
        all_txs = await client.get_transactions(ELECTOR_ADDRESS, limit=5)
        if len(all_txs) < 3:
            pytest.skip("Not enough transactions")
        mid_lt = all_txs[2].lt
        filtered = await client.get_transactions(ELECTOR_ADDRESS, limit=5, to_lt=mid_lt)
        for tx in filtered:
            assert tx.lt > mid_lt

    async def test_nonexistent_returns_empty(self, client):
        txs = await client.get_transactions(NONEXISTENT_ADDRESS, limit=5)
        assert txs == []


class TestGetConfig:
    async def test_contains_standard_params(self, client):
        config = await client.get_config()
        for key in (0, 1, 4, 34):
            assert key in config, f"Config param {key} missing"


class TestRunGetMethod:
    async def test_returns_int(self, client):
        stack = await client.run_get_method(ELECTOR_ADDRESS, "active_election_id")
        assert len(stack) >= 1
        assert isinstance(stack[0], int)

    async def test_nonexistent_method_raises(self, client):
        with pytest.raises(RunGetMethodError) as exc_info:
            await client.run_get_method(ELECTOR_ADDRESS, "nonexistent_method_xyz")
        assert exc_info.value.exit_code != 0
