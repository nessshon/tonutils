from __future__ import annotations

from ton_core import Address, Cell

from tests.constants import (
    EDITABLE_COLLECTION_ADDRESS,
    EDITABLE_NFT_ADDRESS,
    NFT_COLLECTION_ADDRESS,
    NFT_ITEM_ADDRESS,
    SBT_NFT_ADDRESS,
)
from tonutils.contracts.nft import (
    get_authority_address_get_method,
    get_collection_data_get_method,
    get_editor_get_method,
    get_nft_address_by_index_get_method,
    get_nft_content_get_method,
    get_nft_data_get_method,
    get_revoked_time_get_method,
    royalty_params_get_method,
)


class TestGetCollectionData:
    async def test_structure(self, client):
        stack = await get_collection_data_get_method(client, NFT_COLLECTION_ADDRESS)
        assert len(stack) == 3
        next_item_index, content, owner_address = stack
        assert isinstance(next_item_index, int)
        assert next_item_index > 0
        assert isinstance(content, Cell)
        assert isinstance(owner_address, Address)


class TestGetNFTAddressByIndex:
    async def test_returns_address(self, client):
        addr = await get_nft_address_by_index_get_method(client, NFT_COLLECTION_ADDRESS, index=0)
        assert isinstance(addr, Address)

    async def test_different_indexes(self, client):
        addr_0 = await get_nft_address_by_index_get_method(client, NFT_COLLECTION_ADDRESS, index=0)
        addr_1 = await get_nft_address_by_index_get_method(client, NFT_COLLECTION_ADDRESS, index=1)
        assert addr_0 != addr_1


class TestGetNFTData:
    async def test_structure(self, client):
        stack = await get_nft_data_get_method(client, NFT_ITEM_ADDRESS)
        assert len(stack) == 5
        init_flag, index, collection_address, owner_address, content = stack
        assert isinstance(init_flag, int)
        assert init_flag in (0, -1)
        assert isinstance(index, int)
        assert index >= 0
        assert isinstance(collection_address, Address)
        assert isinstance(owner_address, Address)
        assert isinstance(content, Cell)

    async def test_item_points_to_collection(self, client):
        stack = await get_nft_data_get_method(client, NFT_ITEM_ADDRESS)
        assert stack[2] == Address(NFT_COLLECTION_ADDRESS)


class TestRoyaltyParams:
    async def test_structure(self, client):
        stack = await royalty_params_get_method(client, NFT_COLLECTION_ADDRESS)
        assert len(stack) == 3
        numerator, denominator, destination = stack
        assert isinstance(numerator, int)
        assert numerator >= 0
        assert isinstance(denominator, int)
        assert denominator > 0
        assert isinstance(destination, Address)


class TestGetEditor:
    async def test_returns_address(self, client):
        result = await get_editor_get_method(client, EDITABLE_NFT_ADDRESS)
        assert isinstance(result, Address)


class TestGetNFTContent:
    async def test_returns_cell(self, client):
        nft_stack = await get_nft_data_get_method(client, EDITABLE_NFT_ADDRESS)
        index = nft_stack[1]
        individual_content = nft_stack[4]
        result = await get_nft_content_get_method(client, EDITABLE_COLLECTION_ADDRESS, index, individual_content)
        assert isinstance(result, Cell)


class TestGetAuthorityAddress:
    async def test_returns_address(self, client):
        result = await get_authority_address_get_method(client, SBT_NFT_ADDRESS)
        assert isinstance(result, Address)


class TestGetRevokedTime:
    async def test_returns_int(self, client):
        result = await get_revoked_time_get_method(client, SBT_NFT_ADDRESS)
        assert isinstance(result, int)
        assert result >= 0
