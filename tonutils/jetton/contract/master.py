from typing import Union

from pytoniq_core import Cell, begin_cell, Address, Slice

from .wallet import JettonWallet
from ..content import JettonOffchainContent, JettonOnchainContent
from ..data import JettonMasterData
from ..op_codes import *
from ...client import Client, TonapiClient, ToncenterClient, LiteClient
from ...contract import Contract
from ...exceptions import UnknownClientError
from ...utils import boc_to_base64_string


class JettonMaster(Contract):
    CODE_HEX = "b5ee9c7241020b010001ed000114ff00f4a413f4bcf2c80b0102016202030202cc040502037a60090a03efd9910e38048adf068698180b8d848adf07d201800e98fe99ff6a2687d007d206a6a18400aa9385d47181a9aa8aae382f9702480fd207d006a18106840306b90fd001812881a28217804502a906428027d012c678b666664f6aa7041083deecbef29385d71811a92e001f1811802600271812f82c207f97840607080093dfc142201b82a1009aa0a01e428027d012c678b00e78b666491646580897a007a00658064907c80383a6465816503e5ffe4e83bc00c646582ac678b28027d0109e5b589666664b8fd80400fe3603fa00fa40f82854120870542013541403c85004fa0258cf1601cf16ccc922c8cb0112f400f400cb00c9f9007074c8cb02ca07cbffc9d05008c705f2e04a12a1035024c85004fa0258cf16ccccc9ed5401fa403020d70b01c3008e1f8210d53276db708010c8cb055003cf1622fa0212cb6acb1fcb3fc98042fb00915be200303515c705f2e049fa403059c85004fa0258cf16ccccc9ed54002e5143c705f2e049d43001c85004fa0258cf16ccccc9ed54007dadbcf6a2687d007d206a6a183618fc1400b82a1009aa0a01e428027d012c678b00e78b666491646580897a007a00658064fc80383a6465816503e5ffe4e840001faf16f6a2687d007d206a6a183faa904051007f09"  # noqa

    def __init__(
            self,
            client: Client,
            content: Union[JettonOffchainContent, JettonOnchainContent],
            admin_address: Union[Address, str],
            jetton_wallet_code: Union[str, Cell] = JettonWallet.CODE_HEX,
    ) -> None:
        self.client = client

        self._data = self.create_data(content, admin_address, jetton_wallet_code).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            content: Union[JettonOffchainContent, JettonOnchainContent],
            admin_address: Union[Address, str, None],
            jetton_wallet_code: Union[str, Cell] = JettonWallet.CODE_HEX,
    ) -> JettonMasterData:
        return JettonMasterData(
            admin_address=admin_address,
            content=content,
            jetton_wallet_code=jetton_wallet_code,
        )

    @classmethod
    async def get_jetton_data(
            cls,
            client: Client,
            jetton_master_address: Union[Address, str],
    ) -> JettonMasterData:
        """
        Get the data of the jetton master.

        :param client: The client to use.
        :param jetton_master_address: The address of the jetton master.
        :return: The data of the jetton master.
        """
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        if isinstance(client, TonapiClient):
            method_result = await client.run_get_method(
                address=jetton_master_address.to_str(),
                method_name="get_jetton_data",
            )
            total_supply = int(method_result["stack"][0]["num"], 16)
            mintable = bool(int(method_result["stack"][1]["num"], 16))
            admin_address = Slice.one_from_boc(method_result["stack"][2]["cell"]).load_address()
            content = Slice.one_from_boc(method_result["stack"][3]["cell"])
            jetton_wallet_code = Cell.one_from_boc(method_result["stack"][4]["cell"])

        elif isinstance(client, ToncenterClient):
            method_result = await client.run_get_method(
                address=jetton_master_address.to_str(),
                method_name="get_jetton_data",
            )
            total_supply = int(method_result["stack"][0]["value"], 16)
            mintable = bool(method_result["stack"][1]["value"])
            admin_address = Slice.one_from_boc(method_result["stack"][2]["value"]).load_address()
            content = Slice.one_from_boc(method_result["stack"][3]["value"])
            jetton_wallet_code = Cell.one_from_boc(method_result["stack"][4]["value"])

        elif isinstance(client, LiteClient):
            method_result = await client.run_get_method(
                address=jetton_master_address.to_str(),
                method_name="get_jetton_data",
            )
            print(method_result)
            total_supply = int(method_result[0])
            mintable = bool(method_result[1])
            admin_address = method_result[2].load_address()
            content = method_result[3]
            jetton_wallet_code = method_result[4]

        else:
            raise UnknownClientError(client.__class__.__name__)

        return JettonMasterData(
            total_supply=total_supply,
            mintable=mintable,
            admin_address=admin_address,
            content=content,
            jetton_wallet_code=jetton_wallet_code,
        )

    @classmethod
    async def get_wallet_address(
            cls,
            client: Client,
            owner_address: Union[Address, str],
            jetton_master_address: Union[Address, str],
    ) -> Address:
        """
        Get the address of the jetton wallet.

        :param client: The client to use.
        :param owner_address: The address of the owner.
        :param jetton_master_address: The address of the jetton master.
        :return: The address of the jetton wallet.
        """
        if isinstance(owner_address, str):
            owner_address = Address(owner_address)

        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        if isinstance(client, TonapiClient):
            method_result = await client.run_get_method(
                address=jetton_master_address.to_str(),
                method_name="get_wallet_address",
                stack=[owner_address.to_str()],
            )
            result = Address(method_result["decoded"]["jetton_wallet_address"])

        elif isinstance(client, ToncenterClient):
            method_result = await client.run_get_method(
                address=jetton_master_address.to_str(),
                method_name="get_wallet_address",
                stack=[boc_to_base64_string(begin_cell().store_address(owner_address).end_cell().to_boc())],
            )
            result = Slice.one_from_boc(method_result["stack"][0]["value"]).load_address()

        elif isinstance(client, LiteClient):
            method_result = await client.run_get_method(
                address=jetton_master_address.to_str(),
                method_name="get_wallet_address",
                stack=[Address(owner_address).to_cell().to_slice()],
            )
            result = method_result[0].load_address()

        else:
            raise UnknownClientError(client.__class__.__name__)

        return result

    @classmethod
    def build_mint_body(
            cls,
            destination: Address,
            jetton_amount: int,
            amount: int = 20000000,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the mint transaction.

        :param destination: The address of the destination.
        :param jetton_amount: The amount of jettons to be minted.
        :param amount: The amount of coins in nanoton. Defaults to 20000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the mint transaction.
        """
        return (
            begin_cell()
            .store_uint(JETTON_MINT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(destination)
            .store_coins(amount)
            .store_maybe_ref(
                begin_cell()
                .store_uint(JETTON_INTERNAL_TRANSFER_OPCODE, 32)
                .store_uint(query_id, 64)
                .store_coins(jetton_amount)
                .store_address(None)
                .store_address(None)
                .store_bit(0)
                .store_coins(0)
                .store_bit(0)
                .end_cell()
            )
            .end_cell()
        )

    @classmethod
    def build_edit_content_body(
            cls,
            new_content: Union[JettonOffchainContent, JettonOnchainContent],
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the edit content transaction.

        :param new_content: The new content.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the edit content transaction.
        """
        return (
            begin_cell()
            .store_uint(JETTON_EDIT_CONTENT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_ref(new_content.serialize())
            .end_cell()
        )

    @classmethod
    def build_change_admin_body(
            cls,
            new_admin_address: Address,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the change admin transaction.

        :param new_admin_address: The address of the new admin.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the change admin transaction.
        """
        return (
            begin_cell()
            .store_uint(JETTON_CHANGE_ADMIN_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(new_admin_address)
            .end_cell()
        )
