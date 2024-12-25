from typing import Tuple

from pytoniq_core import Address, Cell, begin_cell
from typing_extensions import Optional

from tonutils.client import Client
from tonutils.jetton import JettonMaster
from .constants import *


class StonfiPTONV2:

    def __init__(self, client: Client, pton_address: Optional[Address] = None) -> None:
        self.client = client
        self.address = pton_address or Address(
            PTONAddresses.TESTNET
            if client.is_testnet else
            PTONAddresses.MAINNET
        )
        self.is_testnet = client.is_testnet

    @classmethod
    def build_ton_transfer_body(
            cls,
            ton_amount: int,
            refund_address: Address,
            forward_payload: Optional[Cell] = None,
            query_id: int = 0,
    ) -> Cell:
        cell = (
            begin_cell()
            .store_uint(OpCodes.TON_TRANSFER, 32)
            .store_uint(query_id, 64)
            .store_coins(ton_amount)
            .store_address(refund_address)
        )

        if forward_payload is not None:
            cell.store_bit(True)
            cell.store_ref(forward_payload)

        return cell.end_cell()

    @classmethod
    def build_deploy_wallet_body(
            cls,
            owner_address: Address,
            excess_address: Address,
            query_id: int = 0,
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(OpCodes.DEPLOY_WALLET, 32)
            .store_uint(query_id, 64)
            .store_address(owner_address)
            .store_address(excess_address)
            .end_cell()
        )

    async def get_ton_transfer_tx_params(
            self,
            ton_amount: int,
            destination_address: Address,
            refund_address: Address,
            forward_payload: Optional[Cell] = None,
            forward_ton_amount: int = 0,
            query_id: int = 0,
    ) -> Tuple[Address, int, Cell]:
        to = await JettonMaster.get_wallet_address(
            client=self.client,
            owner_address=destination_address,
            jetton_master_address=self.address,
        )

        body = self.build_ton_transfer_body(
            ton_amount=ton_amount,
            refund_address=refund_address,
            forward_payload=forward_payload,
            query_id=query_id,
        )

        value = ton_amount + forward_ton_amount + GasConstants.TON_TRANSFER

        return to, value, body

    async def get_deploy_wallet_tx_params(
            self,
            owner_address: Address,
            excess_address: Address,
            gas_amount: Optional[int] = None,
            query_id: int = 0,
    ) -> Tuple[Address, Cell, Cell]:
        to = self.address

        body = self.build_deploy_wallet_body(
            owner_address=owner_address,
            excess_address=excess_address,
            query_id=query_id,
        )

        value = gas_amount or GasConstants.DEPLOY_WALLET

        return to, body, value
