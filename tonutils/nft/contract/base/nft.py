from __future__ import annotations

from typing import Optional, Union

from pytoniq_core import Address, Cell, Slice, begin_cell

from ...data import NFTData
from ...op_codes import *
from ....client import Client, TonapiClient, ToncenterClient, LiteClient
from ....contract import Contract
from ....exceptions import UnknownClientError


class NFT(Contract):

    @classmethod
    async def get_nft_data(
            cls,
            client: Client,
            nft_address: Union[Address, str],
    ) -> NFTData:
        if isinstance(nft_address, str):
            nft_address = Address(nft_address)

        if isinstance(client, TonapiClient):
            method_result = await client.run_get_method(
                address=nft_address.to_str(),
                method_name="get_nft_data",
            )
            index = method_result["decoded"]["index"]
            owner_address = Address(method_result["decoded"]["owner_address"])
            collection_address = Address(method_result["decoded"]["collection_address"])
            content = Slice.one_from_boc(method_result["decoded"]["individual_content"]).load_snake_string()

        elif isinstance(client, ToncenterClient):
            method_result = await client.run_get_method(
                address=nft_address.to_str(),
                method_name="get_nft_data",
            )
            index = int(method_result["stack"][1]["value"], 16)
            collection_address = Slice.one_from_boc(method_result["stack"][2]["value"]).load_address()
            owner_address = Slice.one_from_boc(method_result["stack"][3]["value"]).load_address()
            content = Slice.one_from_boc(method_result["stack"][4]["value"]).load_snake_string()

        elif isinstance(client, LiteClient):
            method_result = await client.run_get_method(
                address=nft_address.to_str(),
                method_name="get_nft_data",
            )
            index = int(method_result[1])
            collection_address = method_result[2].load_address()
            owner_address = method_result[3].load_address()
            content = method_result[4].begin_parse().load_snake_string()

        else:
            raise UnknownClientError(client.__class__.__name__)

        return NFTData(index, collection_address, owner_address, content)

    @classmethod
    def build_transfer_body(
            cls,
            new_owner_address: Address,
            response_address: Optional[Address] = None,
            custom_payload: Optional[Cell] = None,
            forward_payload: Optional[Cell] = None,
            forward_amount: int = 0,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the transfer nft transaction.

        :param new_owner_address: The new owner address.
        :param response_address: The address for the response (the sender's address is specified).
            If the address is specified, the excess of TON is returned to the specified address;
            otherwise, it remains on the token contract.
        :param custom_payload: Custom payload for the transaction.
        :param forward_payload: Forward payload for the transaction.
            If forward_amount is greater than 0, this payload will be included with the notification to the new owner.
        :param forward_amount: Forward amount. Defaults to 0.
            A notification will be sent to the new owner if the amount is greater than 0;
            otherwise, the new owner will not receive a notification.
        :param query_id: The query ID. Defaults to 0.
        """
        return (
            begin_cell()
            .store_uint(TRANSFER_NFT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(new_owner_address)
            .store_address(response_address or new_owner_address)
            .store_maybe_ref(custom_payload)
            .store_coins(forward_amount)
            .store_maybe_ref(forward_payload)
            .end_cell()
        )
