import typing as t

from pytoniq_core import Address, Cell

from ...protocols import ClientProtocol


class NFTCollectionGetMethods:

    @classmethod
    async def get_collection_data(
        cls,
        client: ClientProtocol,
        address: Address,
    ) -> t.List[t.Any]:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_collection_data",
        )
        return method_result

    @classmethod
    async def get_nft_address_by_index(
        cls,
        client: ClientProtocol,
        address: Address,
        index: int,
    ) -> Address:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_nft_address_by_index",
            stack=[index],
        )
        return method_result[0]

    @classmethod
    async def royalty_params(
        cls,
        client: ClientProtocol,
        address: Address,
    ) -> t.List[t.Any]:
        method_result = await client.run_get_method(
            address=address,
            method_name="royalty_params",
        )
        return method_result

    @classmethod
    async def get_nft_content(
        cls,
        client: ClientProtocol,
        address: Address,
        index: int,
        individual_nft_content: Cell,
    ) -> Cell:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_nft_content",
            stack=[index, individual_nft_content],
        )
        return method_result[0]

    @classmethod
    async def get_second_owner_address(
        cls,
        client: ClientProtocol,
        address: Address,
    ) -> Address:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_second_owner_address",
        )
        return method_result[0]


class NFTItemGetMethods:

    @classmethod
    async def get_nft_data(
        cls,
        client: ClientProtocol,
        address: Address,
    ) -> t.List[t.Any]:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_nft_data",
        )
        return method_result

    @classmethod
    async def get_editor(
        cls,
        client: ClientProtocol,
        address: Address,
    ) -> t.Optional[Address]:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_editor",
        )
        return method_result[0]

    @classmethod
    async def get_authority_address(
        cls,
        client: ClientProtocol,
        address: Address,
    ) -> t.Optional[Address]:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_authority_address",
        )
        return method_result[0]

    @classmethod
    async def get_revoked_time(
        cls,
        client: ClientProtocol,
        address: Address,
    ) -> int:
        method_result = await client.run_get_method(
            address=address,
            method_name="get_revoked_time",
        )
        return method_result[0]
