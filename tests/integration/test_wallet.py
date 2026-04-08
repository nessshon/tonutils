from __future__ import annotations

from ton_core import Cell, PublicKey

from tests.constants import (
    HIGHLOAD_V3R1_ADDRESS,
    WALLET_ADDRESS,
    WALLET_V4R2_ADDRESS,
    WALLET_V5R1_ADDRESS,
)
from tonutils.contracts.wallet import (
    get_extensions_get_method,
    get_last_clean_time_get_method,
    get_plugin_list_get_method,
    get_public_key_get_method,
    get_subwallet_id_get_method,
    get_timeout_get_method,
    is_signature_allowed_get_method,
    seqno_get_method,
)


class TestSeqno:
    async def test_returns_positive_int(self, client):
        result = await seqno_get_method(client, WALLET_ADDRESS)
        assert isinstance(result, int)
        assert result > 0


class TestGetPublicKey:
    async def test_returns_public_key(self, client):
        result = await get_public_key_get_method(client, WALLET_ADDRESS)
        assert isinstance(result, PublicKey)


class TestGetSubwalletId:
    async def test_returns_int(self, client):
        result = await get_subwallet_id_get_method(client, WALLET_V4R2_ADDRESS)
        assert isinstance(result, int)


class TestGetPluginList:
    async def test_returns_list(self, client):
        result = await get_plugin_list_get_method(client, WALLET_V4R2_ADDRESS)
        assert isinstance(result, list)


class TestIsSignatureAllowed:
    async def test_returns_bool(self, client):
        result = await is_signature_allowed_get_method(client, WALLET_V5R1_ADDRESS)
        assert isinstance(result, bool)


class TestGetExtensions:
    async def test_returns(self, client):
        result = await get_extensions_get_method(client, WALLET_V5R1_ADDRESS)
        assert result is None or isinstance(result, (Cell, list))


class TestHighloadGetPublicKey:
    async def test_returns_public_key(self, client):
        result = await get_public_key_get_method(client, HIGHLOAD_V3R1_ADDRESS)
        assert isinstance(result, PublicKey)


class TestHighloadGetLastCleanTime:
    async def test_returns_int(self, client):
        result = await get_last_clean_time_get_method(client, HIGHLOAD_V3R1_ADDRESS)
        assert isinstance(result, int)
        assert result >= 0


class TestHighloadGetTimeout:
    async def test_returns_positive_int(self, client):
        result = await get_timeout_get_method(client, HIGHLOAD_V3R1_ADDRESS)
        assert isinstance(result, int)
        assert result > 0
