import time
from typing import Optional, Tuple

from pytoniq_core import Address, Cell, begin_cell

from tonutils.client import Client
from tonutils.jetton import JettonMaster, JettonWallet
from .constants import *
from ..pton.pton import StonfiPTONV2


class StonfiRouterV2:

    def __init__(
            self,
            client: Client,
            router_address: Optional[Address] = None,
            pton_address: Optional[Address] = None,
    ) -> None:
        self.client = client
        self.router_address = router_address or Address(
            RouterAddresses.TESTNET
            if client.is_testnet else
            RouterAddresses.MAINNET
        )
        self.pton = StonfiPTONV2(client, pton_address)
        self.is_testnet = client.is_testnet

    @classmethod
    def default_deadline(cls) -> int:
        return int(time.time()) + TX_DEADLINE

    @classmethod
    def build_swap_body(
            cls,
            ask_jetton_wallet_address: Address,
            receiver_address: Address,
            min_ask_amount: int,
            refund_address: Address,
            excesses_address: Optional[Address] = None,
            dex_custom_payload: Optional[Cell] = None,
            dex_custom_payload_forward_gas_amount: int = 0,
            refund_payload: Optional[Cell] = None,
            refund_forward_gas_amount: int = 0,
            referral_address: Optional[Address] = None,
            referral_value: Optional[int] = None,
            deadline: Optional[int] = None,
    ) -> Cell:
        if referral_value:
            assert 0 <= referral_value <= 100, "'referralValue' should be in range [0, 100] BPS"

        return (
            begin_cell()
            .store_uint(OpCodes.SWAP, 32)
            .store_address(ask_jetton_wallet_address)
            .store_address(refund_address)
            .store_address(excesses_address or refund_address)
            .store_uint(deadline or cls.default_deadline(), 64)
            .store_ref(
                begin_cell()
                .store_coins(min_ask_amount)
                .store_address(receiver_address)
                .store_coins(dex_custom_payload_forward_gas_amount)
                .store_maybe_ref(dex_custom_payload)
                .store_coins(refund_forward_gas_amount)
                .store_maybe_ref(refund_payload)
                .store_uint(referral_value or 10, 16)
                .store_address(referral_address)
                .end_cell()
            )
            .end_cell()
        )

    @classmethod
    def build_cross_swap_body(
            cls,
            ask_jetton_wallet_address: Address,
            receiver_address: Address,
            min_ask_amount: int,
            refund_address: Address,
            excesses_address: Optional[Address] = None,
            dex_custom_payload: Optional[Cell] = None,
            dex_custom_payload_forward_gas_amount: int = 0,
            refund_payload: Optional[Cell] = None,
            refund_forward_gas_amount: int = 0,
            referral_address: Optional[Address] = None,
            referral_value: Optional[int] = None,
            deadline: Optional[int] = None,
    ) -> Cell:
        if referral_value:
            assert 0 <= referral_value <= 100, "'referralValue' should be in range [0, 100] BPS"

        return (
            begin_cell()
            .store_uint(OpCodes.CROSS_SWAP, 32)
            .store_address(ask_jetton_wallet_address)
            .store_address(refund_address)
            .store_address(excesses_address or refund_address)
            .store_uint(deadline or cls.default_deadline(), 64)
            .store_ref(
                begin_cell()
                .store_coins(min_ask_amount)
                .store_address(receiver_address)
                .store_coins(dex_custom_payload_forward_gas_amount)
                .store_maybe_ref(dex_custom_payload)
                .store_coins(refund_forward_gas_amount)
                .store_maybe_ref(refund_payload)
                .store_uint(referral_value or 10, 16)
                .store_address(referral_address)
                .end_cell()
            )
            .end_cell()
        )

    async def get_swap_jetton_to_jetton_tx_params(
            self,
            user_wallet_address: Address,
            receiver_address: Address,
            offer_jetton_address: Address,
            ask_jetton_address: Address,
            offer_amount: int,
            min_ask_amount: int,
            refund_address: Address,
            excesses_address: Optional[Address] = None,
            referral_address: Optional[Address] = None,
            referral_value: Optional[int] = None,
            dex_custom_payload: Optional[Cell] = None,
            dex_custom_payload_forward_gas_amount: int = 0,
            refund_payload: Optional[Cell] = None,
            refund_forward_gas_amount: int = 0,
            deadline: Optional[int] = None,
            gas_amount: Optional[int] = None,
            forward_gas_amount: Optional[int] = None,
            query_id: int = 0,
            jetton_custom_payload: Optional[Cell] = None,
    ) -> Tuple[Address, int, Cell]:
        contract_address = self.router_address

        offer_jetton_wallet_address = await JettonMaster.get_wallet_address(
            client=self.client,
            owner_address=user_wallet_address,
            jetton_master_address=offer_jetton_address,
        )
        ask_jetton_wallet_address = await JettonMaster.get_wallet_address(
            client=self.client,
            owner_address=contract_address,
            jetton_master_address=ask_jetton_address,
        )

        forward_ton_amount = forward_gas_amount or GasConstants.swap_jetton_to_jetton.FORWARD_GAS_AMOUNT

        forward_payload = self.build_swap_body(
            ask_jetton_wallet_address=ask_jetton_wallet_address,
            receiver_address=receiver_address or user_wallet_address,
            min_ask_amount=min_ask_amount,
            refund_address=refund_address or user_wallet_address,
            excesses_address=excesses_address,
            referral_address=referral_address,
            referral_value=referral_value,
            dex_custom_payload=dex_custom_payload,
            dex_custom_payload_forward_gas_amount=dex_custom_payload_forward_gas_amount,
            refund_payload=refund_payload,
            refund_forward_gas_amount=refund_forward_gas_amount,
            deadline=deadline,
        )

        body = JettonWallet.build_transfer_body(
            jetton_amount=offer_amount,
            recipient_address=contract_address,
            response_address=user_wallet_address,
            custom_payload=jetton_custom_payload,
            forward_amount=forward_ton_amount,
            forward_payload=forward_payload,
            query_id=query_id,
        )

        value = gas_amount or GasConstants.swap_jetton_to_jetton.GAS_AMOUNT

        return offer_jetton_wallet_address, value, body

    async def get_swap_jetton_to_ton_tx_params(
            self,
            user_wallet_address: Address,
            receiver_address: Address,
            offer_jetton_address: Address,
            offer_amount: int,
            min_ask_amount: int,
            refund_address: Address,
            excesses_address: Optional[Address] = None,
            referral_address: Optional[Address] = None,
            referral_value: Optional[int] = None,
            dex_custom_payload: Optional[Cell] = None,
            dex_custom_payload_forward_gas_amount: int = 0,
            refund_payload: Optional[Cell] = None,
            refund_forward_gas_amount: int = 0,
            deadline: Optional[int] = None,
            gas_amount: Optional[int] = None,
            forward_gas_amount: Optional[int] = None,
            query_id: int = 0,
            jetton_custom_payload: Optional[Cell] = None,
    ) -> tuple[Address, int, Cell]:
        return await self.get_swap_jetton_to_jetton_tx_params(
            user_wallet_address=user_wallet_address,
            receiver_address=receiver_address,
            offer_jetton_address=offer_jetton_address,
            ask_jetton_address=self.pton.address,
            offer_amount=offer_amount,
            min_ask_amount=min_ask_amount,
            refund_address=refund_address,
            excesses_address=excesses_address,
            referral_address=referral_address,
            referral_value=referral_value,
            dex_custom_payload=dex_custom_payload,
            dex_custom_payload_forward_gas_amount=dex_custom_payload_forward_gas_amount,
            refund_payload=refund_payload,
            refund_forward_gas_amount=refund_forward_gas_amount,
            deadline=deadline,
            gas_amount=gas_amount or GasConstants.swap_jetton_to_ton.GAS_AMOUNT,
            forward_gas_amount=forward_gas_amount or GasConstants.swap_jetton_to_ton.FORWARD_GAS_AMOUNT,
            query_id=query_id,
            jetton_custom_payload=jetton_custom_payload,
        )

    async def get_swap_ton_to_jetton_tx_params(
            self,
            user_wallet_address: Address,
            receiver_address: Address,
            offer_jetton_address: Address,
            offer_amount: int,
            min_ask_amount: int,
            refund_address: Address,
            excesses_address: Optional[Address] = None,
            referral_address: Optional[Address] = None,
            referral_value: Optional[int] = None,
            dex_custom_payload: Optional[Cell] = None,
            dex_custom_payload_forward_gas_amount: int = 0,
            refund_payload: Optional[Cell] = None,
            refund_forward_gas_amount: int = 0,
            deadline: Optional[int] = None,
            forward_gas_amount: Optional[int] = None,
            query_id: int = 0,
    ) -> tuple[Address, int, Cell]:
        contract_address = self.router_address

        ask_jetton_wallet_address = await JettonMaster.get_wallet_address(
            client=self.client,
            owner_address=contract_address,
            jetton_master_address=offer_jetton_address,
        )

        forward_payload = self.build_swap_body(
            ask_jetton_wallet_address=ask_jetton_wallet_address,
            receiver_address=receiver_address or user_wallet_address,
            min_ask_amount=min_ask_amount,
            refund_address=refund_address or user_wallet_address,
            excesses_address=excesses_address,
            referral_address=referral_address,
            referral_value=referral_value,
            dex_custom_payload=dex_custom_payload,
            dex_custom_payload_forward_gas_amount=dex_custom_payload_forward_gas_amount,
            refund_payload=refund_payload,
            refund_forward_gas_amount=refund_forward_gas_amount,
            deadline=deadline,
        )

        forward_ton_amount = forward_gas_amount or GasConstants.swap_ton_to_jetton.FORWARD_GAS_AMOUNT

        return await self.pton.get_ton_transfer_tx_params(
            ton_amount=offer_amount,
            destination_address=contract_address,
            refund_address=user_wallet_address,
            forward_payload=forward_payload,
            forward_ton_amount=forward_ton_amount,
            query_id=query_id,
        )
