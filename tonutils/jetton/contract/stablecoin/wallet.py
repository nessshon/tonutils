from typing import Union, Optional

from pytoniq_core import Address, Cell, begin_cell

from .op_codes import *
from ...data import JettonWalletStablecoinData
from ....client import (
    Client,
)
from ....contract import Contract


class JettonWalletStablecoin(Contract):
    # https://github.com/OpenBuilders/notcoin-contract/blob/main/contracts/jetton-wallet.fc
    CODE_HEX = "b5ee9c7241020f01000380000114ff00f4a413f4bcf2c80b01020162050202012004030021bc508f6a2686981fd007d207d2068af81c0027bfd8176a2686981fd007d207d206899fc152098402f8d001d0d3030171b08e48135f038020d721ed44d0d303fa00fa40fa40d104d31f01840f218210178d4519ba0282107bdd97deba12b1f2f48040d721fa003012a0401303c8cb0358fa0201cf1601cf16c9ed54e0fa40fa4031fa0031f401fa0031fa00013170f83a02d31f012082100f8a7ea5ba8e85303459db3ce0330c06025c228210178d4519ba8e84325adb3ce034218210595f07bcba8e843101db3ce0135f038210d372158cbadc840ff2f0080701f2ed44d0d303fa00fa40fa40d106d33f0101fa00fa40f401d15141a15238c705f2e04926c2fff2afc882107bdd97de01cb1f5801cb3f01fa0221cf1658cf16c9c8801801cb0526cf1670fa02017158cb6accc903f839206e9430811703de718102f270f8380170f836a0811a6570f836a0bcf2b0028050fb00030903e8ed44d0d303fa00fa40fa40d107d33f0101fa00fa40fa4053bac705f82a5464e070546004131503c8cb0358fa0201cf1601cf16c921c8cb0113f40012f400cb00c9f9007074c8cb02ca07cbffc9d0500cc7051bb1f2e04a5152a009fa0021925f04e30d22d70b01c000b3953010246c31e30d50030b0a09002003c8cb0358fa0201cf1601cf16c9ed5400785054a1f82fa07381040982100966018070f837b60972fb02c8801001cb0501cf1670fa027001cb6a8210d53276db01cb1f5801cb3fc9810082fb00010060c882107362d09c01cb1f2501cb3f5004fa0258cf1658cf16c9c8801001cb0524cf1658fa02017158cb6accc98011fb0001f603d33f0101fa00fa4021fa4430c000f2e14ded44d0d303fa00fa40fa40d1521ac705f2e0495115a120c2fff2aff82a54259070546004131503c8cb0358fa0201cf1601cf16c921c8cb0113f40012f400cb00c920f9007074c8cb02ca07cbffc9d004fa40f401fa002020d70b009ad74bc00101c001b0f2b19130e20d01fec88210178d451901cb1f500a01cb3f5008fa0223cf1601cf1626fa025007cf16c9c8801801cb055004cf1670fa024063775003cb6bccccc945372191729171e2f839206e938127519120e2216e94318128c39101e25023a813a0738103a370f83ca00270f83612a00170f836a07381040982100966018070f837a0bcf2b0040e002a8050fb005803c8cb0358fa0201cf1601cf16c9ed54d28ef7c1"  # noqa

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
    ) -> JettonWalletStablecoinData:
        return JettonWalletStablecoinData(
            owner_address=owner_address,
            jetton_master_address=jetton_master_address,
            balance=balance,
        )

    @classmethod
    async def get_wallet_data(
            cls,
            client: Client,
            jetton_wallet_address: Union[Address, str],
    ) -> JettonWalletStablecoinData:
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

        return JettonWalletStablecoinData(
            balance=balance,
            owner_address=owner_address,
            jetton_master_address=jetton_master_address,
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
