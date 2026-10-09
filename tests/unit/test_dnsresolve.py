from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from ton_core import Address, DNSCategory, DNSRecordDNSNextResolver, DNSRecordWallet, NetworkGlobalID

from tests.constants import ZERO_ADDRESS
from tonutils.clients import ToncenterClient
from tonutils.exceptions import ProviderResponseError, RunGetMethodError

ROOT = Address(ZERO_ADDRESS)
NEXT_RESOLVER = DNSRecordDNSNextResolver(ZERO_ADDRESS).serialize()


def _make_client(*results: object) -> ToncenterClient:
    client = ToncenterClient(network=NetworkGlobalID.TESTNET)
    client.run_get_method = AsyncMock(side_effect=list(results))  # type: ignore[method-assign]
    return client


async def _resolve(client: ToncenterClient) -> object:
    return await client.dnsresolve("alice.ton", DNSCategory.WALLET, ROOT)


class TestDnsresolve:
    async def test_wallet_record(self):
        record = DNSRecordWallet(ZERO_ADDRESS).serialize()
        client = _make_client([32, NEXT_RESOLVER], [48, record])
        result = await _resolve(client)
        assert isinstance(result, DNSRecordWallet)

    async def test_null_record_as_empty_list(self):
        client = _make_client([32, NEXT_RESOLVER], [48, []])
        assert await _resolve(client) is None

    @pytest.mark.parametrize(
        "error",
        [
            RunGetMethodError(address=ZERO_ADDRESS, exit_code=-256, method_name="dnsresolve"),
            ProviderResponseError(code=404, message="entity not found", endpoint="test"),
        ],
    )
    async def test_unregistered_domain(self, error: Exception):
        client = _make_client([32, NEXT_RESOLVER], error)
        assert await _resolve(client) is None

    async def test_provider_failure_propagates(self):
        error = ProviderResponseError(code=500, message="internal error", endpoint="test")
        client = _make_client([32, NEXT_RESOLVER], error)
        with pytest.raises(ProviderResponseError):
            await _resolve(client)
