from typing import Union

from pytoniq_core import Address

from tonutils.cache import async_cache
from tonutils.client import Client
from tonutils.contract import Contract
from tonutils.jetton.data import JettonMasterData


class JettonMaster(Contract):

    @classmethod
    async def get_jetton_data(
            cls,
            client: Client,
            jetton_master_address: Union[Address, str],
    ) -> JettonMasterData:
        """
        Get the data of the jetton master.

        :param client: The client to use.
        :param jetton_master_address: The address of the jetton master.
        :return: The data of the jetton master.
        """
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        method_result = await client.run_get_method(
            address=jetton_master_address.to_str(),
            method_name="get_jetton_data",
        )

        total_supply = method_result[0]
        mintable = bool(method_result[1])
        admin_address = method_result[2]
        content = method_result[3]
        jetton_wallet_code = method_result[4]

        return JettonMasterData(
            total_supply=total_supply,
            mintable=mintable,
            admin_address=admin_address,
            content=content,
            jetton_wallet_code=jetton_wallet_code,
        )

    @classmethod
    @async_cache()
    async def get_wallet_address(
            cls,
            client: Client,
            owner_address: Union[Address, str],
            jetton_master_address: Union[Address, str],
    ) -> Address:
        """
        Get the address of the jetton wallet.

        :param client: The client to use.
        :param owner_address: The address of the owner.
        :param jetton_master_address: The address of the jetton master.
        :return: The address of the jetton wallet.
        """
        if isinstance(owner_address, str):
            owner_address = Address(owner_address)

        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        method_result = await client.run_get_method(
            address=jetton_master_address.to_str(),
            method_name="get_wallet_address",
            stack=[owner_address],
        )

        return method_result[0]
