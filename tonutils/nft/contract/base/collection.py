from __future__ import annotations

from typing import Union

from pytoniq_core import Address

from ...royalty_params import RoyaltyParams
from ....client import Client
from ....contract import Contract


class Collection(Contract):

    @classmethod
    async def get_royalty_params(
            cls,
            client: Client,
            collection_address: Union[Address, str],
    ) -> RoyaltyParams:
        """
        Gets the royalty parameters of the collection.

        :param client: The client instance.
        :param collection_address: The address of the collection.
        :return: The royalty parameters of the collection.
        """
        if isinstance(collection_address, str):
            collection_address = Address(collection_address)

        method_result = await client.run_get_method(
            address=collection_address.to_str(),
            method_name="royalty_params",
        )
        base = method_result[0]
        factor = method_result[1]
        royalty_address = method_result[2]

        return RoyaltyParams(base, factor, royalty_address)
