import typing as t

from pytoniq_core import Address

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import AddressLike


async def get_jetton_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """
    Get Jetton master contract data.

    :param client: TON client for blockchain interactions
    :param address: Jetton master contract address
    :return: List containing total_supply, mintable, admin_address, jetton_content, and jetton_wallet_code
    """
    return await client.run_get_method(
        address=address,
        method_name="get_jetton_data",
    )


class GetJettonDataGetMethod(ContractProtocol):
    """Mixin providing get_jetton_data() get method for Jetton master contracts."""

    async def get_jetton_data(self) -> t.List[t.Any]:
        """
        Get Jetton master contract data.

        Returns total supply, mintable flag, admin address, content, and wallet code.

        :return: List containing total_supply, mintable, admin_address, jetton_content, and jetton_wallet_code
        """
        return await get_jetton_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_wallet_address_get_method(
    client: ClientProtocol,
    address: AddressLike,
    owner_address: AddressLike,
) -> Address:
    """
    Get Jetton wallet address for a specific owner.

    :param client: TON client for blockchain interactions
    :param address: Jetton master contract address
    :param owner_address: Owner's wallet address (Address or string)
    :return: Address of the Jetton wallet contract for this owner
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
    """Mixin providing get_wallet_address() get method for Jetton master contracts."""

    async def get_wallet_address(
        self,
        owner_address: AddressLike,
    ) -> Address:
        """
        Get Jetton wallet address for a specific owner.

        :param owner_address: Owner's wallet address (Address or string)
        :return: Address of the Jetton wallet contract for this owner
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
    """
    Get next admin address from a Jetton master contract.

    :param client: TON client for blockchain interactions
    :param address: Jetton master contract address
    :return: Address of the next admin if set, None otherwise
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_next_admin_address",
    )
    return t.cast(t.Optional[Address], r[0])


class GetNextAdminAddressGetMethod(ContractProtocol):
    """Mixin providing get_next_admin_address() get method for Jetton master contracts."""

    async def get_next_admin_address(self) -> t.Optional[Address]:
        """
        Get next admin address from this Jetton master contract.

        Used during admin transfer process.

        :return: Address of the next admin if set, None otherwise
        """
        return await get_next_admin_address_get_method(
            client=self.client,
            address=self.address,
        )


async def get_wallet_data_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> t.List[t.Any]:
    """
    Get Jetton wallet data.

    :param client: TON client for blockchain interactions
    :param address: Jetton wallet contract address
    :return: List containing balance, owner, jetton_master_address, and jetton_wallet_code
    """
    return await client.run_get_method(
        address=address,
        method_name="get_wallet_data",
    )


class GetWalletDataGetMethod(ContractProtocol):
    """Mixin providing get_wallet_data() get method for Jetton wallet contracts."""

    async def get_wallet_data(self) -> t.List[t.Any]:
        """
        Get Jetton wallet data.

        Returns balance, owner address, Jetton master address, and wallet code.

        :return: List containing balance, owner, jetton_master_address, and jetton_wallet_code
        """
        return await get_wallet_data_get_method(
            client=self.client,
            address=self.address,
        )


async def get_status_get_method(
    client: ClientProtocol,
    address: AddressLike,
) -> int:
    """
    Get status from a contract.

    :param client: TON client for blockchain interactions
    :param address: Contract address
    :return: Status code
    """
    r = await client.run_get_method(
        address=address,
        method_name="get_status",
    )
    return int(r[0])


class GetStatusGetMethod(ContractProtocol):
    """Mixin providing get_status() get method for contracts."""

    async def get_status(self) -> int:
        """
        Get status from this contract.

        :return: Status code
        """
        return await get_status_get_method(
            client=self.client,
            address=self.address,
        )
