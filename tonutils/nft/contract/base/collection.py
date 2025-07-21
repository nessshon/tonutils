from __future__ import annotations

from typing import Union

from pytoniq_core import Address, Slice

from ...royalty_params import RoyaltyParams
from ....client import Client, TonapiClient, ToncenterClient, LiteserverClient
from ....contract import Contract
from ....exceptions import UnknownClientError


def get_gas_fee():
    # https://github.com/sweet-io-org/miniapp-nft-contracts/blob/c32e737066291ec6a7c7e64ce4bf42a7c64fe4ce/contracts/standard_nft_purchase.fc#L46
    return 200000000  # 0.015 TON for messages and mint


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

        if isinstance(client, TonapiClient):
            method_result = await client.run_get_method(
                address=collection_address.to_str(),
                method_name="royalty_params",
            )
            base = int(method_result["decoded"]["numerator"])
            factor = int(method_result["decoded"]["denominator"])
            royalty_address = Address(method_result["decoded"]["destination"])

        elif isinstance(client, ToncenterClient):
            method_result = await client.run_get_method(
                address=collection_address.to_str(),
                method_name="royalty_params",
            )
            base = int(method_result["stack"][0]["value"], 16)
            factor = int(method_result["stack"][1]["value"], 16)
            royalty_address = Slice.one_from_boc(method_result["stack"][2]["value"]).load_address()

        elif isinstance(client, LiteserverClient):
            method_result = await client.run_get_method(
                address=collection_address.to_str(),
                method_name="royalty_params",
            )
            base = int(method_result[0])
            factor = int(method_result[1])
            royalty_address = method_result[2].load_address()

        else:
            raise UnknownClientError(client.__class__.__name__)

        return RoyaltyParams(base, factor, royalty_address)

