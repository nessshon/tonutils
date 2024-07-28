from __future__ import annotations

from typing import Optional

from pytoniq_core import Address, Cell, begin_cell

from ..op_codes import *
from ...contract import Contract


class Item(Contract):

    @classmethod
    def build_transfer_body(
            cls,
            new_owner_address: Address,
            response_address: Optional[Address] = None,
            custom_payload: Optional[Cell] = Cell.empty(),
            forward_payload: Optional[Cell] = Cell.empty(),
            forward_amount: Optional[int] = 0,
            query_id: Optional[int] = 0,
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(TRANSFER_ITEM_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(new_owner_address)
            .store_address(response_address or new_owner_address)
            .store_maybe_ref(custom_payload)
            .store_coins(forward_amount)
            .store_maybe_ref(forward_payload)
            .end_cell()
        )

    @classmethod
    def build_ownership_assigned_body(
            cls,
            prev_owner_address: Address,
            forward_payload: Optional[Cell] = Cell.empty(),
            query_id: Optional[int] = 0,
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(OWNERSHIP_ASSIGNED_ITEM_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(prev_owner_address)
            .store_maybe_ref(forward_payload)
            .end_cell()
        )
