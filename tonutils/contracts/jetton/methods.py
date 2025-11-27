import typing as t

from pytoniq_core import Address

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike


async def get_jetton_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    return await client.run_get_method(
        address=address,
        method_name="get_jetton_data",
    )


class GetJettonDataGetMethod(ContractProtocol):
    async def get_jetton_data(self) -> t.List[t.Any]:
        return await get_jetton_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_wallet_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
    owner_address: AddressLike,
) -> Address:
    if isinstance(owner_address, str):
        owner_address = Address(owner_address)

    r = await client.run_get_method(
        address=address,
        method_name="get_wallet_address",
        stack=[owner_address],
    )
    return t.cast(Address, r[0])


class GetWalletAddressGetMethod(ContractProtocol):
    async def get_wallet_address(
        self,
        owner_address: AddressLike,
    ) -> Address:
        return await get_wallet_address_get_method(
            client=self.client,
            address=self.address,
            owner_address=owner_address,
        )


async def get_next_admin_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.Optional[Address]:
    r = await client.run_get_method(
        address=address,
        method_name="get_next_admin_address",
    )
    return t.cast(t.Optional[Address], r[0])


class GetNextAdminAddressGetMethod(ContractProtocol):
    async def get_next_admin_address(self) -> t.Optional[Address]:
        return await get_next_admin_address_get_method(
            client=self.client,
            address=self.address,
        )


async def get_wallet_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    return await client.run_get_method(
        address=address,
        method_name="get_wallet_data",
    )


class GetWalletDataGetMethod(ContractProtocol):
    async def get_wallet_data(self) -> t.List[t.Any]:
        return await get_wallet_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_status_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    r = await client.run_get_method(
        address=address,
        method_name="get_status",
    )
    return int(r[0])


class GetStatusGetMethod(ContractProtocol):
    async def get_status(self) -> int:
        return await get_status_get_method(
            client=self.client,
            address=self.address,
        )
