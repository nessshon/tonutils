from __future__ import annotations

from ton_core import Address, Cell

from tests.constants import JETTON_STABLECOIN_ADDRESS, USDT_MASTER_ADDRESS, WALLET_ADDRESS
from tonutils.contracts.jetton import (
    get_jetton_data_get_method,
    get_next_admin_address_get_method,
    get_status_get_method,
    get_wallet_address_get_method,
    get_wallet_data_get_method,
)


class TestGetJettonData:
    async def test_structure(self, client):
        stack = await get_jetton_data_get_method(client, USDT_MASTER_ADDRESS)
        assert len(stack) == 5
        total_supply, mintable, admin_address, content, wallet_code = stack
        assert isinstance(total_supply, int)
        assert total_supply > 0
        assert isinstance(mintable, int)
        assert mintable in (0, -1)
        assert isinstance(admin_address, Address)
        assert isinstance(content, Cell)
        assert isinstance(wallet_code, Cell)


class TestGetWalletAddress:
    async def test_returns_address(self, client):
        addr = await get_wallet_address_get_method(client, USDT_MASTER_ADDRESS, Address(WALLET_ADDRESS))
        assert isinstance(addr, Address)


class TestGetWalletData:
    @staticmethod
    async def _wallet_address(client) -> Address:
        return await get_wallet_address_get_method(client, USDT_MASTER_ADDRESS, Address(WALLET_ADDRESS))

    async def test_structure(self, client):
        wallet_addr = await self._wallet_address(client)
        stack = await get_wallet_data_get_method(client, wallet_addr)
        assert len(stack) == 4
        balance, owner, jetton_master, wallet_code = stack
        assert isinstance(balance, int)
        assert balance >= 0
        assert isinstance(owner, Address)
        assert isinstance(jetton_master, Address)
        assert isinstance(wallet_code, Cell)

    async def test_wallet_points_to_master(self, client):
        wallet_addr = await self._wallet_address(client)
        stack = await get_wallet_data_get_method(client, wallet_addr)
        assert stack[2] == Address(USDT_MASTER_ADDRESS)

    async def test_owner_matches(self, client):
        wallet_addr = await self._wallet_address(client)
        stack = await get_wallet_data_get_method(client, wallet_addr)
        assert stack[1] == Address(WALLET_ADDRESS)


class TestGetNextAdminAddress:
    async def test_returns(self, client):
        result = await get_next_admin_address_get_method(client, USDT_MASTER_ADDRESS)
        assert result is None or isinstance(result, Address)


class TestGetStatus:
    async def test_returns_int(self, client):
        result = await get_status_get_method(client, JETTON_STABLECOIN_ADDRESS)
        assert isinstance(result, int)
