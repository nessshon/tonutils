from __future__ import annotations

from ton_core import Cell, DNSCategory

from tests.constants import DNS_COLLECTION_ADDRESS, DNS_DOMAIN, DNS_ITEM_ADDRESS
from tonutils.contracts.dns import (
    get_auction_info_get_method,
    get_domain_get_method,
    get_last_fill_up_time_get_method,
)
from tonutils.contracts.nft import get_collection_data_get_method


class TestGetDomain:
    async def test_returns_cell(self, client):
        result = await get_domain_get_method(client, DNS_ITEM_ADDRESS)
        assert isinstance(result, Cell)


class TestGetLastFillUpTime:
    async def test_returns_positive_int(self, client):
        result = await get_last_fill_up_time_get_method(client, DNS_ITEM_ADDRESS)
        assert isinstance(result, int)
        assert result > 0


class TestGetAuctionInfo:
    async def test_returns_list(self, client):
        result = await get_auction_info_get_method(client, DNS_ITEM_ADDRESS)
        assert isinstance(result, list)
        assert len(result) >= 3


class TestDNSCollectionData:
    async def test_structure(self, client):
        stack = await get_collection_data_get_method(client, DNS_COLLECTION_ADDRESS)
        assert len(stack) == 3
        assert isinstance(stack[0], int)


class TestDNSResolve:
    async def test_resolves_wallet(self, client):
        result = await client.dnsresolve(DNS_DOMAIN, DNSCategory.WALLET)
        assert result is not None
