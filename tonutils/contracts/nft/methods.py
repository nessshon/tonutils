import typing as t

from pytoniq_core import Address, Cell

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike


async def get_collection_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    return await client.run_get_method(
        address=address,
        method_name="get_collection_data",
    )


class GetCollectionDataGetMethod(ContractProtocol):
    async def get_collection_data(self) -> t.List[t.Any]:
        return await get_collection_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_nft_address_by_index_get_method(
    client: ClientProtocol,
    address: AddressLike,
    index: int,
) -> Address:
    r = await client.run_get_method(
        address=address,
        method_name="get_nft_address_by_index",
        stack=[index],
    )
    return t.cast(Address, r[0])


class GetNFTAddressByIndexGetMethod(ContractProtocol):
    async def get_nft_address_by_index(
        self,
        index: int,
    ) -> Address:
        return await get_nft_address_by_index_get_method(
            client=self.client,
            address=self.address,
            index=index,
        )


async def royalty_params_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    return await client.run_get_method(
        address=address,
        method_name="royalty_params",
    )


class RoyaltyParamsGetMethod(ContractProtocol):
    async def royalty_params(self) -> t.List[t.Any]:
        return await royalty_params_get_method(
            client=self.client,
            address=self.address,
        )


async def get_nft_content_get_method(
    client: ClientProtocol,
    address: AddressLike,
    index: int,
    individual_nft_content: Cell,
) -> Cell:
    r = await client.run_get_method(
        address=address,
        method_name="get_nft_content",
        stack=[index, individual_nft_content],
    )
    return t.cast(Cell, r[0])


class GetNFTContentGetMethod(ContractProtocol):
    async def get_nft_content(
        self,
        index: int,
        individual_nft_content: Cell,
    ) -> Cell:
        return await get_nft_content_get_method(
            client=self.client,
            address=self.address,
            index=index,
            individual_nft_content=individual_nft_content,
        )


async def get_second_owner_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> Address:
    r = await client.run_get_method(
        address=address,
        method_name="get_second_owner_address",
    )
    return t.cast(Address, r[0])


class GetSecondOwnerAddressGetMethod(ContractProtocol):
    async def get_second_owner_address(self) -> Address:
        return await get_second_owner_address_get_method(
            client=self.client,
            address=self.address,
        )


async def get_nft_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    return await client.run_get_method(
        address=address,
        method_name="get_nft_data",
    )


class GetNFTDataGetMethod(ContractProtocol):
    async def get_nft_data(self) -> t.List[t.Any]:
        return await get_nft_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_editor_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.Optional[Address]:
    r = await client.run_get_method(
        address=address,
        method_name="get_editor",
    )
    return t.cast(t.Optional[Address], r[0])


class GetEditorGetMethod(ContractProtocol):
    async def get_editor(self) -> t.Optional[Address]:
        return await get_editor_get_method(
            client=self.client,
            address=self.address,
        )


async def get_authority_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.Optional[Address]:
    r = await client.run_get_method(
        address=address,
        method_name="get_authority_address",
    )
    return t.cast(t.Optional[Address], r[0])


class GetAuthorityAddressGetMethod(ContractProtocol):
    async def get_authority_address(self) -> t.Optional[Address]:
        return await get_authority_address_get_method(
            client=self.client,
            address=self.address,
        )


async def get_revoked_time_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    r = await client.run_get_method(
        address=address,
        method_name="get_revoked_time",
    )
    return int(r[0])


class GetRevokedTimeGetMethod(ContractProtocol):
    async def get_revoked_time(self) -> int:
        return await get_revoked_time_get_method(
            client=self.client,
            address=self.address,
        )
