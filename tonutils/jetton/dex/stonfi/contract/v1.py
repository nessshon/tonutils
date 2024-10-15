from typing import Union, Optional

from pytoniq_core import Address, Cell, begin_cell

from tonutils.jetton import JettonWallet
from tonutils.jetton.dex.stonfi.op_codes import *


class StonfiRouterV1:

    @classmethod
    def build_swap_body(
            cls,
            jetton_amount: int,
            recipient_address: Union[Address, str],
            forward_amount: int,
            user_wallet_address: Union[Address, str],
            min_amount: int,
            ask_jetton_wallet_address: Union[Address, str],
            referral_address: Optional[Union[Address, str]] = None,
    ) -> Cell:
        forward_payload = (
            begin_cell()
            .store_uint(SWAP_V1_OPCODE, 32)
            .store_address(ask_jetton_wallet_address)
            .store_coins(min_amount)
            .store_address(user_wallet_address)
            .store_address(referral_address)
            .store_uint(0 if referral_address is None else 1, 1)
        )

        if referral_address is not None:
            forward_payload.store_address(referral_address)

        return JettonWallet.build_transfer_body(
            jetton_amount=jetton_amount,
            recipient_address=recipient_address,
            response_address=user_wallet_address,
            forward_amount=forward_amount,
            forward_payload=forward_payload.end_cell(),
        )
