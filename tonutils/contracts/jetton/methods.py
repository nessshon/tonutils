import typing as t

from pytoniq_core import Address

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.protocol import ContractProtocol
from tonutils.types import AddressLike


async def get_jetton_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """Call `get_jetton_data` on a Jetton master contract.

    :param client: TON client.
    :param address: Jetton master address.
    :return: List of [total_supply, mintable, admin_address, content, wallet_code].
    """
    return await client.run_get_method(
        address=address,
        method_name="get_jetton_data",
    )


class GetJettonDataGetMethod(ContractProtocol):
    """Mixin for the `get_jetton_data` get-method."""

    async def get_jetton_data(self) -> t.List[t.Any]:
        """Return Jetton master data (supply, mintable, admin, content, code)."""
        return await get_jetton_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_wallet_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
    owner_address: AddressLike,
) -> Address:
    """Call `get_wallet_address` on a Jetton master contract.

    :param client: TON client.
    :param address: Jetton master address.
    :param owner_address: Owner's wallet address.
    :return: Jetton wallet address for the owner.
    """
    if isinstance(owner_address, str):
        owner_address = Address(owner_address)

    r = await client.run_get_method(
        address=address,
        method_name="get_wallet_address",
        stack=[owner_address],
    )
    return t.cast(Address, r[0])


class GetWalletAddressGetMethod(ContractProtocol):
    """Mixin for the `get_wallet_address` get-method."""

    async def get_wallet_address(self, owner_address: AddressLike) -> Address:
        """Return Jetton wallet address for the given owner.

        :param owner_address: Owner's wallet address.
        :return: Jetton wallet address.
        """
        return await get_wallet_address_get_method(
            client=self.client,
            address=self.address,
            owner_address=owner_address,
        )


async def get_next_admin_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.Optional[Address]:
    """Call `get_next_admin_address` on a Jetton master contract.

    :param client: TON client.
    :param address: Jetton master address.
    :return: Next admin address, or `None`.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_next_admin_address",
    )
    return t.cast(t.Optional[Address], r[0])


class GetNextAdminAddressGetMethod(ContractProtocol):
    """Mixin for the `get_next_admin_address` get-method."""

    async def get_next_admin_address(self) -> t.Optional[Address]:
        """Return next admin address, or `None`."""
        return await get_next_admin_address_get_method(
            client=self.client,
            address=self.address,
        )


async def get_wallet_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """Call `get_wallet_data` on a Jetton wallet contract.

    :param client: TON client.
    :param address: Jetton wallet address.
    :return: List of [balance, owner, jetton_master, wallet_code].
    """
    return await client.run_get_method(
        address=address,
        method_name="get_wallet_data",
    )


class GetWalletDataGetMethod(ContractProtocol):
    """Mixin for the `get_wallet_data` get-method."""

    async def get_wallet_data(self) -> t.List[t.Any]:
        """Return Jetton wallet data (balance, owner, master, code)."""
        return await get_wallet_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_status_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """Call `get_status` on a contract.

    :param client: TON client.
    :param address: Contract address.
    :return: Status code.
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_status",
    )
    return int(r[0])


class GetStatusGetMethod(ContractProtocol):
    """Mixin for the `get_status` get-method."""

    async def get_status(self) -> int:
        """Return contract status code."""
        return await get_status_get_method(
            client=self.client,
            address=self.address,
        )
