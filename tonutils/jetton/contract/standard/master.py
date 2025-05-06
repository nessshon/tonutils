from typing import Union

from pytoniq_core import Address, Cell, StateInit, begin_cell

from .op_codes import *
from .wallet import JettonWalletStandard
from ..base import JettonMaster
from ...content import JettonOffchainContent, JettonOnchainContent
from ...data import JettonMasterData


class JettonMasterStandard(JettonMaster):
    CODE_HEX = "b5ee9c7241020b010001ed000114ff00f4a413f4bcf2c80b0102016202030202cc040502037a60090a03efd9910e38048adf068698180b8d848adf07d201800e98fe99ff6a2687d007d206a6a18400aa9385d47181a9aa8aae382f9702480fd207d006a18106840306b90fd001812881a28217804502a906428027d012c678b666664f6aa7041083deecbef29385d71811a92e001f1811802600271812f82c207f97840607080093dfc142201b82a1009aa0a01e428027d012c678b00e78b666491646580897a007a00658064907c80383a6465816503e5ffe4e83bc00c646582ac678b28027d0109e5b589666664b8fd80400fe3603fa00fa40f82854120870542013541403c85004fa0258cf1601cf16ccc922c8cb0112f400f400cb00c9f9007074c8cb02ca07cbffc9d05008c705f2e04a12a1035024c85004fa0258cf16ccccc9ed5401fa403020d70b01c3008e1f8210d53276db708010c8cb055003cf1622fa0212cb6acb1fcb3fc98042fb00915be200303515c705f2e049fa403059c85004fa0258cf16ccccc9ed54002e5143c705f2e049d43001c85004fa0258cf16ccccc9ed54007dadbcf6a2687d007d206a6a183618fc1400b82a1009aa0a01e428027d012c678b00e78b666491646580897a007a00658064fc80383a6465816503e5ffe4e840001faf16f6a2687d007d206a6a183faa904051007f09"  # noqa

    def __init__(
            self,
            content: Union[JettonOffchainContent, JettonOnchainContent],
            admin_address: Union[Address, str],
            jetton_wallet_code: Union[str, Cell] = JettonWalletStandard.CODE_HEX,
    ) -> None:
        self._data = self.create_data(content, admin_address, jetton_wallet_code).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            content: Union[JettonOffchainContent, JettonOnchainContent],
            admin_address: Union[Address, str, None],
            jetton_wallet_code: Union[str, Cell] = JettonWalletStandard.CODE_HEX,
    ) -> JettonMasterData:
        return JettonMasterData(
            admin_address=admin_address,
            content=content,
            jetton_wallet_code=jetton_wallet_code,
        )

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
    def build_change_content_body(
            cls,
            new_content: Union[JettonOffchainContent, JettonOnchainContent],
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the change content transaction.

        :param new_content: The new content.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the edit content transaction.
        """
        return (
            begin_cell()
            .store_uint(JETTON_CHANGE_CONTENT_OPCODE, 32)
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

    @classmethod
    def calculate_user_jetton_wallet_address(
            cls,
            owner_address: Union[Address, str],
            jetton_wallet_code: str,
            jetton_master_address: Union[Address, str],
    ) -> Address:
        if isinstance(owner_address, str):
            owner_address = Address(owner_address)

        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)

        code = Cell.one_from_boc(jetton_wallet_code)
        data = (
            begin_cell()
            .store_coins(0)
            .store_address(owner_address)
            .store_address(jetton_master_address)
            .store_ref(code)
            .end_cell()
        )
        state_init = StateInit(code=code, data=data)

        return Address((0, state_init.serialize().hash))
