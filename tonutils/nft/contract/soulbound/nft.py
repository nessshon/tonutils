from __future__ import annotations

from typing import Optional, Union

from pytoniq_core import Cell, begin_cell, Address

from ..base.nft import NFT
from ...content import NFTOnchainContent, NFTOffchainContent
from ...data import NFTData
from ...op_codes import *


class NFTSoulbound(NFT):
    # https://github.com/nessshon/nft-contracts/blob/main/soulbound/func/nft-item.func
    CODE_HEX = "b5ee9c724102130100033b000114ff00f4a413f4bcf2c80b0102016202030202cc04050201200f1002012006070037dfc23fc237c20e4659ffc21e78b7c22678b667c22e78b659fe4f6aa404bdd361110638048adf000e86981fd20187803fc2159c70e18fc2180e382f970cafd2000fc326a00fc337d20187c32b87c33f8047001698f8138d8718100e99fc1086861dff529185d71814108026f68a429185d718118410817e5935129105d408090a0b0061f76a268699f80fc30fd2000fc31b87c31106ba4e100470b3ffc317d2000fc326a00fc337d2000fc32e99f987c33c89871400943031d31f82100524c7ae12ba8e39d33f308010f844708210c18e86d255036d804003c8cb1f12cb3f216eb39301cf179131e2c97105c8cb055004cf1658fa0213cb6accc901fb009130e200c26c12fa40d4d30030f847f841c8cbff5006cf16f844cf1612cc14cb3f5230cb0003c30096f8465003cc02de801078b17082100dd607e3403514804003c8cb1f12cb3f216eb39301cf179131e2c97105c8cb055004cf1658fa0213cb6accc901fb0000c632f8445003c705f2e191fa40d4d30030f847f841c8cbfff844cf1613cc12cb3f5210cb0001c30094f84601ccde801078b17082100524c7ae405503804003c8cb1f12cb3f216eb39301cf179131e2c97105c8cb055004cf1658fa0213cb6accc901fb0003fa8e4031f841c8cbfff843cf1680107082108b7717354015504403804003c8cb1f12cb3f216eb39301cf179131e2c97105c8cb055004cf1658fa0213cb6accc901fb00e082101f04537a5220bae30282106f89f5e35220ba8e165bf84501c705f2e191f847c000f2e193f823f867f008e08210d136d3b35220bae30230310c0d0e009231f84422c705f2e1918010708210d53276db102455026d830603c8cb1f12cb3f216eb39301cf179131e2c97105c8cb055004cf1658fa0213cb6accc901fb008b02f8648b02f865f008008e31f84422c705f2e191820afaf08070fb028010708210d53276db102455026d830603c8cb1f12cb3f216eb39301cf179131e2c97105c8cb055004cf1658fa0213cb6accc901fb00002082105fcc3d14ba93f2c19dde840ff2f00201581112001dbc7e7f803fc217c20fc21fc227c234000db5631e00ff08b0000db7b07e00ff08f0fdaac013"  # noqa

    def __init__(
            self,
            index: int,
            collection_address: Optional[Address] = None,
            owner_address: Optional[Address] = None,
            content: Optional[Union[NFTOnchainContent, NFTOffchainContent]] = None,
    ) -> None:
        self._data = self.create_data(index, collection_address, owner_address, content).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            index: int,
            collection_address: Address,
            owner_address: Optional[Address] = None,
            content: Optional[Union[NFTOnchainContent, NFTOffchainContent]] = None,
    ) -> NFTData:
        return NFTData(
            index=index,
            collection_address=collection_address,
            owner_address=owner_address,
            content=content,
        )

    @classmethod
    def build_revoke_body(cls, query_id: int = 0) -> Cell:
        """
        Builds the body of the revoke nft transaction.

        :param query_id: The query ID. Defaults to 0.
        :param query_id: int, optional
        :return: The cell representing the body of the revoke nft transaction.
        """
        return (
            begin_cell()
            .store_uint(REVOKE_NFT_OPCODE, 32)
            .store_uint(query_id, 64)
            .end_cell()
        )

    @classmethod
    def build_destroy_body(cls, query_id: int = 0) -> Cell:
        """
        Builds the body of the destroy nft transaction.

        :param query_id: The query ID. Defaults to 0.
        :param query_id: int, optional
        :return: The cell representing the body of the destroy nft transaction.
        """
        return (
            begin_cell()
            .store_uint(DESTROY_NFT_OPCODE, 32)
            .store_uint(query_id, 64)
            .end_cell()
        )

    @classmethod
    def build_transfer_body(
            cls,
            new_owner_address: Address,
            response_address: Optional[Address] = None,
            custom_payload: Optional[Cell] = None,
            forward_payload: Optional[Cell] = None,
            forward_amount: int = 0,
            query_id: int = 0,
    ) -> Cell:
        raise NotImplementedError("`Transfer nft` is not supported in the SoulBound NFT Contract.")
