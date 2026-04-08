from __future__ import annotations

from ton_core import ContractState

from tests.constants import ELECTOR_ADDRESS, USDT_MASTER_ADDRESS
from tonutils.contracts.base import BaseContract


class TestFromAddress:
    async def test_load_state_true(self, client):
        contract = await BaseContract.from_address(client, USDT_MASTER_ADDRESS, load_state=True)
        assert contract.info.state == ContractState.ACTIVE
        assert contract.info.balance > 0
        assert contract.info.code_raw is not None

    async def test_load_state_false(self, client):
        contract = await BaseContract.from_address(client, USDT_MASTER_ADDRESS, load_state=False)
        assert contract.address is not None
        assert contract._info is None


class TestRefresh:
    async def test_loads_state(self, client):
        contract = await BaseContract.from_address(client, ELECTOR_ADDRESS, load_state=False)
        assert contract._info is None
        await contract.refresh()
        assert contract.info.state == ContractState.ACTIVE
        assert contract.info.balance > 0
