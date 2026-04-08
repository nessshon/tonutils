from __future__ import annotations

from ton_core import Cell

from tests.constants import TELEGRAM_USERNAME_NFT_ADDRESS
from tonutils.contracts.telegram import get_full_domain_get_method, get_telemint_token_name_get_method


class TestGetFullDomain:
    async def test_returns_cell(self, client):
        result = await get_full_domain_get_method(client, TELEGRAM_USERNAME_NFT_ADDRESS)
        assert isinstance(result, Cell)


class TestGetTelemintTokenName:
    async def test_returns_cell(self, client):
        result = await get_telemint_token_name_get_method(client, TELEGRAM_USERNAME_NFT_ADDRESS)
        assert isinstance(result, Cell)
