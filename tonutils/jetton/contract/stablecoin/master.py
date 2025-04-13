from typing import Union, Optional

from pytoniq_core import Cell, begin_cell, Address

from .op_codes import *
from .wallet import JettonWalletStablecoin
from ...content import JettonStablecoinContent
from ...data import JettonMasterData, JettonMasterStablecoinData
from ....client import (
    Client,
)
from ....contract import Contract


class JettonMasterStablecoin(Contract):
    # https://github.com/OpenBuilders/notcoin-contract/blob/main/contracts/jetton-minter.fc
    CODE_HEX = "b5ee9c7241021601000494000114ff00f4a413f4bcf2c80b0102016207020201200603020271050400cfaf16f6a2687d007d207d206a6a68bf99e836c1783872ebdb514d9c97c283b7f0ae5179029e2b6119c39462719e4f46ed8f7413e62c780a417877407e978f01a40711411b1acb773a96bdd93fa83bb5ca8435013c8c4b3ac91f4589cc780a38646583fa0064a180400085adbcf6a2687d007d207d206a6a688a2f827c1400b82a3002098a81e46581ac7d0100e78b00e78b6490e4658089fa00097a00658064fc80383a6465816503e5ffe4e8400025bd9adf6a2687d007d207d206a6a6888122f8240202cb0908001da23864658380e78b64814183fa0bc002f5d0cb434c0c05c6c238ecc200835c874c7c0608405e351466ea44c38601035c87e800c3b51343e803e903e90353534541168504d3214017e809400f3c58073c5b333327b55383e903e900c7e800c7d007e800c7e80004c5c3e0e80b4c7c04074cfc044bb51343e803e903e9035353449a084190adf41eeb8c08e496130a03f682107bdd97deba8ee53505fa00fa40f82854120770546004131503c8cb0358fa0201cf1601cf16c921c8cb0113f40012f400cb00c9f9007074c8cb02ca07cbffc9d05008c705f2e04a12a144145036c85005fa025003cf1601cf16ccccc9ed54fa40d120d70b01c000b3915be30de02582102c76b973bae302342412100b04fe82106501f354ba8e2130335142c705f2e04902fa40d1400304c85005fa025003cf1601cf16ccccc9ed54e0248210fb88e119ba8e20313303d15131c705f2e0498b024034c85005fa025003cf1601cf16ccccc9ed54e02482107431f221bae30237238210cb862902bae302365b2082102508d66abae3026c318210d372158c0f0e0d0c000cbadc840ff2f0001e3002c705f2e049d4d4d101ed54fb040044335142c705f2e049c85003cf16c9134440c85005fa025003cf1601cf16ccccc9ed54004430335042c705f2e04901d18b028b024034c85005fa025003cf1601cf16ccccc9ed5401fe355f033401fa40d2000101d195c821cf16c9916de2c8801001cb055004cf1670fa027001cb6a8210d173540001cb1f500401cb3f23fa4430c0008e35f828440470546004131503c8cb0358fa0201cf1601cf16c921c8cb0113f40012f400cb00c9f9007074c8cb02ca07cbffc9d012cf1697316c127001cb01e2f400c98050110004fb000044c8801001cb0501cf1670fa027001cb6a8210d53276db01cb1f0101cb3fc98042fb00019635355161c705f2e04904fa4021fa4430c000f2e14dfa00d4d120d0d31f018210178d4519baf2e0488040d721fa00fa4031fa4031fa0020d70b009ad74bc00101c001b0f2b19130e254431b14018e2191729171e2f839206e938127519120e2216e94318128c39101e25023a813a0738103a370f83ca00270f83612a00170f836a07381040982100966018070f837a0bcf2b025597f1500ea820898968070fb02f828450470546004131503c8cb0358fa0201cf1601cf16c921c8cb0113f40012f400cb00c920f9007074c8cb02ca07cbffc9d0c8801801cb0501cf1658fa02029858775003cb6bcccc9730017158cb6acce2c98011fb005005a04314c85005fa025003cf1601cf16ccccc9ed543399faac"  # noqa

    def __init__(
            self,
            content: JettonStablecoinContent,
            admin_address: Union[Address, str],
            transfer_admin_address: Optional[Union[Address, str]] = None,
            jetton_wallet_code: Union[str, Cell] = JettonWalletStablecoin.CODE_HEX,
    ) -> None:
        self._data = self.create_data(content, admin_address, transfer_admin_address, jetton_wallet_code).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            content: JettonStablecoinContent,
            admin_address: Optional[Union[Address, str]] = None,
            transfer_admin_address: Optional[Union[Address, str]] = None,
            jetton_wallet_code: Union[str, Cell] = JettonWalletStablecoin.CODE_HEX,
    ) -> JettonMasterStablecoinData:
        return JettonMasterStablecoinData(
            admin_address=admin_address,
            transfer_admin_address=transfer_admin_address,
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

        method_result = await client.run_get_method(
            address=jetton_master_address.to_str(),
            method_name="get_jetton_data",
        )

        total_supply = method_result[0]
        mintable = bool(method_result[1])
        admin_address = method_result[2]
        content = method_result[3]
        jetton_wallet_code = method_result[4]

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

        method_result = await client.run_get_method(
            address=jetton_master_address.to_str(),
            method_name="get_wallet_address",
            stack=[owner_address],
        )
        return method_result[0]

    @classmethod
    def build_mint_body(
            cls,
            destination: Address,
            jetton_amount: int,
            amount: int = 100000000,
            forward_amount: int = 50000000,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the mint transaction.

        :param destination: The address of the destination.
        :param jetton_amount: The amount of jettons to be minted.
        :param amount: The amount of coins in nanoton. Defaults to 100000000.
        :param forward_amount: The amount of coins in nanoton. Defaults to 50000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the mint transaction.
        """
        return (
            begin_cell()
            .store_uint(JETTON_MINT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(destination)
            .store_coins(amount)
            .store_ref(
                begin_cell()
                .store_uint(JETTON_INTERNAL_TRANSFER_OPCODE, 32)
                .store_uint(query_id, 64)
                .store_coins(jetton_amount)
                .store_address(None)
                .store_address(None)
                .store_coins(forward_amount)
                .store_bit(0)
                .end_cell()
            )
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

    @classmethod
    def build_drop_admin_body(
            cls,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the drop admin transaction.

        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the drop admin transaction.
        """
        return (
            begin_cell()
            .store_uint(JETTON_DROP_ADMIN_OPCODE, 32)
            .store_uint(query_id, 64)
            .end_cell()
        )

    @classmethod
    def build_change_content_body(
            cls,
            new_content: JettonStablecoinContent,
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
            .store_uint(JETTON_CHANGE_METADATA_URI_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_snake_string(new_content.uri)
            .end_cell()
        )

    @classmethod
    def build_upgrade_message_body(
            cls,
            new_code: Cell,
            new_data: Cell,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the upgrade contract message transaction.

        :param new_code: The new code cell.
        :param new_data: The new data cell.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the upgrade contract message transaction.
        """
        return (
            begin_cell()
            .store_uint(JETTON_UPGRADE_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_ref(new_data)
            .store_ref(new_code)
            .end_cell()
        )
