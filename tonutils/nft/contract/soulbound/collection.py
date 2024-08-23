from __future__ import annotations

from typing import List, Tuple, Optional

from pytoniq_core import Address, Cell, begin_cell, HashMap

from .nft import NFTSoulbound
from ..base.collection import Collection
from ...content import OffchainContent, OffchainCommonContent
from ...data import CollectionData
from ...op_codes import *
from ...royalty_params import RoyaltyParams


class CollectionSoulbound(Collection):
    CODE_HEX = "b5ee9c724102140100021f000114ff00f4a413f4bcf2c80b0102016202030202cd04050201200e0f04e7d10638048adf000e8698180b8d848adf07d201800e98fe99ff6a2687d20699fea6a6a184108349e9ca829405d47141baf8280e8410854658056b84008646582a802e78b127d010a65b509e58fe59f80e78b64c0207d80701b28b9e382f970c892e000f18112e001718112e001f181181981e0024060708090201200a0b00603502d33f5313bbf2e1925313ba01fa00d43028103459f0068e1201a44343c85005cf1613cb3fccccccc9ed54925f05e200a6357003d4308e378040f4966fa5208e2906a4208100fabe93f2c18fde81019321a05325bbf2f402fa00d43022544b30f00623ba9302a402de04926c21e2b3e6303250444313c85005cf1613cb3fccccccc9ed54002c323401fa40304144c85005cf1613cb3fccccccc9ed54003c8e15d4d43010344130c85005cf1613cb3fccccccc9ed54e05f04840ff2f00201200c0d003d45af0047021f005778018c8cb0558cf165004fa0213cb6b12ccccc971fb008002d007232cffe0a33c5b25c083232c044fd003d0032c03260001b3e401d3232c084b281f2fff2742002012010110025bc82df6a2687d20699fea6a6a182de86a182c40043b8b5d31ed44d0fa40d33fd4d4d43010245f04d0d431d430d071c8cb0701cf16ccc980201201213002fb5dafda89a1f481a67fa9a9a860d883a1a61fa61ff480610002db4f47da89a1f481a67fa9a9a86028be09e008e003e00b01a500c6e"  # noqa

    def __init__(
            self,
            owner_address: Address,
            next_item_index: int,
            content: OffchainContent,
            royalty_params: RoyaltyParams,
    ) -> None:
        self._data = self.create_data(owner_address, next_item_index, content, royalty_params).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            owner_address: Address,
            next_item_index: int,
            content: OffchainContent,
            royalty_params: RoyaltyParams,
    ) -> CollectionData:
        return CollectionData(
            owner_address=owner_address,
            next_item_index=next_item_index,
            content=content,
            royalty_params=royalty_params,
            nft_item_code=NFTSoulbound.CODE_HEX,
        )

    @classmethod
    def build_mint_body(
            cls,
            index: int,
            content: OffchainCommonContent,
            owner_address: Address,
            authority_address: Optional[Address] = None,
            revoked_at: int = 0,
            amount: int = 20000000,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the mint transaction.

        :param index: The index of the nft to be minted.
        :param content: The content of the nft to be minted.
        :param owner_address: The address of the owner.
        :param authority_address: The address of the authority. Defaults to the owner address.
        :param revoked_at: The timestamp when the nft is revoked. Defaults to 0.
        :param amount: The amount of coins in nanoton. Defaults to 20000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the mint transaction.
        """
        return (
            begin_cell()
            .store_uint(NFT_MINT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_uint(index, 64)
            .store_coins(amount)
            .store_ref(
                begin_cell()
                .store_address(owner_address)
                .store_ref(content.serialize())
                .store_address(authority_address or owner_address)
                .store_uint(revoked_at, 64)
                .end_cell()
            )
            .end_cell()
        )

    @classmethod
    def build_batch_mint_body(
            cls,
            data: List[Tuple[OffchainCommonContent, Address, Optional[Address], Optional[int]]],
            from_index: int,
            amount_per_one: int = 20000000,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the batch mint transaction.

        :param data: The list of data for minting. Each tuple contains:
            - OffchainCommonContent: The content of the nft to be minted.
            - Address: The address of the owner.
            - Optional[Address]: The address of the authority (if any) defaults to the owner address.
            - int: The timestamp when the nft is revoked. DDefaults to 0.
        :param from_index: The starting index for minting.
        :param amount_per_one: The amount of coins in nanoton per nft. Defaults to 20000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the batch mint transaction.
        """
        items_dict = HashMap(key_size=64)

        for i, (content, owner_address, authority_address, revoked_at) in enumerate(data, start=0):
            items_dict.set_int_key(
                i + from_index,
                begin_cell()
                .store_coins(amount_per_one)
                .store_ref(
                    begin_cell()
                    .store_address(owner_address)
                    .store_address(authority_address or owner_address)
                    .store_uint(revoked_at or 0, 64)
                    .store_ref(content.serialize())
                    .end_cell()
                )
                .end_cell()
            )

        return (
            begin_cell()
            .store_uint(BATCH_NFT_MINT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_dict(items_dict.serialize())
            .end_cell()
        )
