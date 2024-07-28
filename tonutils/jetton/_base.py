import base64
from typing import Optional

from pytoncenter.v3.models import GetMethodParameterInput
from pytoniq_core import Cell, begin_cell, Address, Slice

from .op_codes import *
from ..client import Client, TonapiClient, ToncenterClient, LiteClient
from ..exceptions import UnknownClientError


class Jetton:

    def __init__(
            self,
            client: Client,
    ) -> None:
        self.client = client

    async def get_jetton_wallet_address(self, jetton_master_address: str, owner_address: str) -> Address:
        if isinstance(self.client, TonapiClient):
            result = await self.client.run_get_method(
                address=jetton_master_address, method_name="get_wallet_address", stack=[owner_address],
            )
            address = Address(result.decoded.get("jetton_wallet_address"))

        elif isinstance(self.client, ToncenterClient):
            stack = GetMethodParameterInput(
                type="slice",
                value=base64.b64encode(begin_cell().store_address(owner_address).end_cell().to_boc()).decode(),
            )
            result = await self.client.run_get_method(
                address=jetton_master_address,
                method_name="get_wallet_address",
                stack=[stack],
            )
            address = Slice.one_from_boc(result.stack[0].value).load_address()

        elif isinstance(self.client, LiteClient):
            stack = Address(owner_address).to_cell().to_slice()
            result = await self.client.run_get_method(
                address=jetton_master_address,
                method_name="get_wallet_address",
                stack=[stack],
            )
            address = result[0].load_address()

        else:
            raise UnknownClientError(self.client.__class__.__name__)

        return address

    @classmethod
    def build_transfer_body(
            cls,
            recipient_address: Address,
            jetton_amount: int,
            response_address: Optional[Address] = None,
            custom_payload: Optional[Cell] = Cell.empty(),
            forward_payload: Optional[Cell] = Cell.empty(),
            forward_amount: Optional[int] = 0,
            query_id: Optional[int] = 0,
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(JETTON_TRANSFER_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_coins(jetton_amount)
            .store_address(recipient_address)
            .store_address(response_address or recipient_address)
            .store_maybe_ref(custom_payload)
            .store_coins(forward_amount)
            .store_maybe_ref(forward_payload)
            .end_cell()
        )

    @classmethod
    def build_burn_body(
            cls,
            jetton_amount: int,
            response_address: Optional[Address] = None,
            custom_payload: Optional[Cell] = Cell.empty(),
            query_id: Optional[int] = 0,
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(JETTON_BURN_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_coins(jetton_amount)
            .store_address(response_address)
            .store_maybe_ref(custom_payload)
            .end_cell()
        )

    @classmethod
    def build_change_admin_body(
            cls,
            new_admin_address: Address,
            query_id: Optional[int] = 0,
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(JETTON_CHANGE_ADMIN_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(new_admin_address)
            .end_cell()
        )

    @classmethod
    def build_jetton_excesses_body(cls, query_id: Optional[int] = 0) -> Cell:
        return (
            begin_cell()
            .store_uint(JETTON_EXCESSES_OPCODE, 32)
            .store_uint(query_id, 64)
            .end_cell()
        )
