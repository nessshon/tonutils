from typing import Union, Optional

from pytoniq_core import Address, Cell, begin_cell

from .op_codes import *
from ...data import JettonWalletData
from ....client import (
    Client,
)
from ....contract import Contract


class JettonWalletStandard(Contract):
    CODE_HEX = "b5ee9c7241021201000328000114ff00f4a413f4bcf2c80b0102016202030202cc0405001ba0f605da89a1f401f481f481a8610201d40607020148080900bb0831c02497c138007434c0c05c6c2544d7c0fc02f83e903e900c7e800c5c75c87e800c7e800c00b4c7e08403e29fa954882ea54c4d167c0238208405e3514654882ea58c511100fc02780d60841657c1ef2ea4d67c02b817c12103fcbc2000113e910c1c2ebcb853600201200a0b020120101101f500f4cffe803e90087c007b51343e803e903e90350c144da8548ab1c17cb8b04a30bffcb8b0950d109c150804d50500f214013e809633c58073c5b33248b232c044bd003d0032c032483e401c1d3232c0b281f2fff274013e903d010c7e801de0063232c1540233c59c3e8085f2dac4f3208405e351467232c7c6600c03f73b51343e803e903e90350c0234cffe80145468017e903e9014d6f1c1551cdb5c150804d50500f214013e809633c58073c5b33248b232c044bd003d0032c0327e401c1d3232c0b281f2fff274140371c1472c7cb8b0c2be80146a2860822625a020822625a004ad822860822625a028062849f8c3c975c2c070c008e00d0e0f009acb3f5007fa0222cf165006cf1625fa025003cf16c95005cc2391729171e25008a813a08208989680aa008208989680a0a014bcf2e2c504c98040fb001023c85004fa0258cf1601cf16ccc9ed5400705279a018a182107362d09cc8cb1f5230cb3f58fa025007cf165007cf16c9718018c8cb0524cf165006fa0215cb6a14ccc971fb0010241023000e10491038375f040076c200b08e218210d53276db708010c8cb055008cf165004fa0216cb6a12cb1f12cb3fc972fb0093356c21e203c85004fa0258cf1601cf16ccc9ed5400db3b51343e803e903e90350c01f4cffe803e900c145468549271c17cb8b049f0bffcb8b0a0822625a02a8005a805af3cb8b0e0841ef765f7b232c7c572cfd400fe8088b3c58073c5b25c60063232c14933c59c3e80b2dab33260103ec01004f214013e809633c58073c5b3327b55200083200835c87b51343e803e903e90350c0134c7e08405e3514654882ea0841ef765f784ee84ac7cb8b174cfcc7e800c04e81408f214013e809633c58073c5b3327b55205eccf23d"  # noqa

    def __init__(
            self,
            owner_address: Union[Address, str],
            jetton_master_address: Union[Address, str],
            balance: int = 0,
    ) -> None:
        self._data = self.create_data(owner_address, jetton_master_address, balance).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            owner_address: Union[Address, str],
            jetton_master_address: Union[Address, str],
            balance: int = 0,
    ) -> JettonWalletData:
        return JettonWalletData(
            owner_address=owner_address,
            jetton_master_address=jetton_master_address,
            jetton_wallet_code=JettonWalletStandard.CODE_HEX,
            balance=balance,
        )

    @classmethod
    async def get_wallet_data(
            cls,
            client: Client,
            jetton_wallet_address: Union[Address, str],
    ) -> JettonWalletData:
        """
        Get the data of the jetton wallet.

        :param client: The client to use.
        :param jetton_wallet_address: The address of the jetton wallet.
        :return: The data of the jetton wallet.
        """
        if isinstance(jetton_wallet_address, str):
            jetton_wallet_address = Address(jetton_wallet_address)

        method_result = await client.run_get_method(
            address=jetton_wallet_address.to_str(),
            method_name="get_wallet_data",
        )
        balance = method_result[0]
        owner_address = method_result[1]
        jetton_master_address = method_result[2]
        jetton_wallet_code = method_result[3]

        return JettonWalletData(
            balance=balance,
            owner_address=owner_address,
            jetton_master_address=jetton_master_address,
            jetton_wallet_code=jetton_wallet_code,
        )

    @classmethod
    def build_transfer_body(
            cls,
            jetton_amount: int,
            recipient_address: Optional[Address],
            response_address: Optional[Address] = None,
            custom_payload: Optional[Cell] = None,
            forward_payload: Optional[Cell] = None,
            forward_amount: int = 0,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the transfer jetton transaction.

        :param jetton_amount: The amount of jettons to transfer.
        :param recipient_address: The address of the recipient.
        :param response_address: The address to respond to. Defaults to the recipient address.
        :param custom_payload: The custom payload. Defaults to an empty cell.
        :param forward_payload: The payload to be forwarded. Defaults to an empty cell.
        :param forward_amount: The amount of coins to be forwarded. Defaults to 0.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the transfer jetton transaction.
        """
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
            custom_payload: Optional[Cell] = None,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the burn jetton transaction.

        :param jetton_amount: The amount of jettons to burn.
        :param response_address: The address to respond to. Defaults to the owner address.
        :param custom_payload: The custom payload. Defaults to an empty cell.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the burn jetton transaction.
        """
        return (
            begin_cell()
            .store_uint(JETTON_BURN_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_coins(jetton_amount)
            .store_address(response_address)
            .store_maybe_ref(custom_payload)
            .end_cell()
        )
