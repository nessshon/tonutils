from typing import Union

from pytoniq_core import Address, Cell, begin_cell, StateInit

from ..data import SaleV3R3Data
from ..op_codes import *
from ....op_codes import TRANSFER_NFT_OPCODE
from .....contract import Contract


class SaleV3R3(Contract):
    CODE_HEX = "b5ee9c7201020f01000393000114ff00f4a413f4bcf2c80b0102016202030202cd04050201200d0e02f7d00e8698180b8d8492f82707d201876a2686980698ffd207d207d207d006a698fe99f9818382985638060004a9885698f85ef10e1804a1805699fc708c5b31b0b731b2b64166382c939996f2805f115e000c92f877012eba4e10116408115dd15e0009159d8d829e4e382d87181156000f968ca164108363610405d4060701d166084017d7840149828148c2fbcb87089343e903e803e903e800c14e4a848685421e845a814a4087e9116dc20043232c15400f3c5807e80b2dab25c7ec00970800975d27080ac2386d411487e9116dc20043232c15400f3c5807e80b2dab25c7ec00408e48d0d3896a0c006430316cb2d430d0d307218020b0f2d19522c3008e14810258f8235341a1bc04f82302a0b913b0f2d1969132e201d43001fb0004f053c7c705b08e5d135f03323737373704fa00fa00fa00305321a121a1c101f2d19805d0fa40fa00fa40fa003030c83202cf1658fa0201cf165004fa02c97020104810371045103408c8cb0017cb1f5005cf165003cf1601cf1601fa02cccb1fcb3fc9ed54e0b3e30230313728c003e30228c000e30208c00208090a0b0086353b3b5374c705925f0be05173c705f2e1f4821005138d9118baf2e1f5fa403010481037553208c8cb0017cb1f5005cf165003cf1601cf1601fa02cccb1fcb3fc9ed5400e23839821005f5e10018bef2e1c95346c7055152c70515b1f2e1ca702082105fcc3d14218010c8cb0528cf1621fa02cb6acb1f15cb3f27cf1627cf1614ca0023fa0213ca00c98306fb0071705417005e331034102308c8cb0017cb1f5005cf165003cf1601cf1601fa02cccb1fcb3fc9ed54001836371038476514433070f005002098554410241023f005e05f0a840ff2f000ec21fa445b708010c8cb055003cf1601fa02cb6ac971fb00702082105fcc3d14c8cb1f5230cb3f24cf165004cf1613ca008209c9c380fa0212ca00c9718018c8cb0527cf1670fa02cb6acc25fa445bc98306fb00715560f8230108c8cb0017cb1f5005cf165003cf1601cf1601fa02cccb1fcb3fc9ed540087bce1676a2686980698ffd207d207d207d006a698fe99f982de87d207d007d207d001829a15090d0e080f968cc93fd222d937d222d91fd222dc1082324ac28056000aac040081bee5ef6a2686980698ffd207d207d207d006a698fe99f9801687d207d007d207d001829b15090d0e080f968cd14fd222d947d222d91fd222d85e00085881aaa894"  # noqa

    def __init__(
            self,
            nft_address: Union[Address, str],
            owner_address: Union[Address, str],
            marketplace_address: Union[Address, str],
            marketplace_fee_address: Union[Address, str],
            royalty_address: Union[Address, str],
            marketplace_fee: int,
            royalty_fee: int,
            price: int,
    ) -> None:
        if isinstance(nft_address, str):
            nft_address = Address(nft_address)

        if isinstance(owner_address, str):
            owner_address = Address(owner_address)

        if isinstance(marketplace_address, str):
            marketplace_address = Address(marketplace_address)

        if isinstance(marketplace_fee_address, str):
            marketplace_fee_address = Address(marketplace_fee_address)

        if isinstance(royalty_address, str):
            royalty_address = Address(royalty_address)

        self._data = self.create_data(
            nft_address=nft_address,
            owner_address=owner_address,
            marketplace_address=marketplace_address,
            marketplace_fee_address=marketplace_fee_address,
            royalty_address=royalty_address,
            marketplace_fee=marketplace_fee,
            royalty_fee=royalty_fee,
            price=price,
        ).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            nft_address: Address,
            owner_address: Address,
            marketplace_address: Address,
            marketplace_fee_address: Address,
            royalty_address: Address,
            marketplace_fee: int,
            royalty_fee: int,
            price: int,
    ) -> SaleV3R3Data:
        return SaleV3R3Data(
            nft_address=nft_address,
            owner_address=owner_address,
            marketplace_address=marketplace_address,
            marketplace_fee_address=marketplace_fee_address,
            royalty_address=royalty_address,
            marketplace_fee=marketplace_fee,
            royalty_fee=royalty_fee,
            price=price,
        )

    @classmethod
    def build_sale_body(cls, query_id: int = 0) -> Cell:
        """
        Build a sale body.

        :param query_id: The query id.
        :return: The sale body.
        """
        return (
            begin_cell()
            .store_uint(ACCEPT_DEPLOY_OPCODE, 32)
            .store_uint(query_id, 64)
            .end_cell()
        )

    @classmethod
    def build_transfer_nft_body(
            cls,
            destination: Address,
            owner_address: Address,
            state_init: StateInit,
            amount: int = 200000000,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the transfer nft transaction.

        :param destination: The destination address.
        :param owner_address: The owner address.
        :param state_init: State init data.
        :param amount: Forward amount. Defaults to 0.2.
        :param query_id: The query ID. Defaults to 0.
        """
        return (
            begin_cell()
            .store_uint(TRANSFER_NFT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(destination)
            .store_address(owner_address)
            .store_bit(0)
            .store_coins(amount)
            .store_uint(DO_SALE_OPCODE, 32)
            .store_ref(state_init.serialize())
            .store_ref(cls.build_sale_body())
            .end_cell()
        )

    @classmethod
    def build_change_price_body(
            cls,
            marketplace_fee: int,
            royalty_fee: int,
            price: int,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the change price transaction.

        :param marketplace_fee: The marketplace fee.
        :param royalty_fee: The royalty fee.
        :param price: The new price in nanoTON.
        :param query_id: The query ID. Defaults to 0.
        """
        return (
            begin_cell()
            .store_uint(CHANGE_PRICE_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_coins(price)
            .store_coins(marketplace_fee)
            .store_coins(royalty_fee)
            .end_cell()
        )

    @classmethod
    def build_cancel_sale_body(cls, query_id: int = 0) -> Cell:
        """
        Builds the body of the cancel sale transaction.

        :param query_id: The query ID. Defaults to 0.
        :return: The cancel sale body.
        """
        return (
            begin_cell()
            .store_uint(CANCEL_SALE_OPCODE, 32)
            .store_uint(query_id, 64)
            .end_cell()
        )
