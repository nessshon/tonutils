from __future__ import annotations

from typing import List, Tuple, Optional, Union

from pytoniq_core import Address, Cell, begin_cell, HashMap

from .nft import NFTEditable
from ..base.collection import Collection
from ...content import (
    CollectionOnchainContent,
    CollectionOffchainContent,
    NFTOnchainContent,
    NFTOffchainContent,
)
from ...data import CollectionData
from ...op_codes import *
from ...royalty_params import RoyaltyParams


class CollectionEditable(Collection):
    # https://github.com/nessshon/nft-contracts/blob/main/editable/func/nft-collection.func
    CODE_HEX = "b5ee9c72410216010002f8000114ff00f4a413f4bcf2c80b0102016202030202cc04050201200e0f02f7d90638048adf000e8698180b8d848adf07d201800e98fe99ff6a2687d20699fa9906380e0004a187d2000ef00ea6a6a182a814108349e9ca829485d47148b2f83360968410854658056b84008646582a802e78b127d010a65b509e58fe59f80e78b64c0207d807029cae382a9d0e382d8f970c8946000f181146001406070201480a0b007037373703d33f5312bbf2e1925312ba01fa00d43029103459f00b8e18a45044451503c85006cf1614cb3f12cccccc01cf16c9ed54925f06e202fc8e753737377004d45350c701c0009430d201309131e28e45018040f4966fa524c0ff25c001b193315250de208e2908a4208100fabe93f2c18fde81019321a05327bbf2f402fa00d43022544d30f00b25ba9304a404de06926c21e2b312e65b335044451503c85006cf1614cb3f12cccccc01cf16c9ed54e028c003e302280809005030363606810fa103c70512f2f401fa40305423055033c85006cf1614cb3f12cccccc01cf16c9ed5400eec0048e20313235353501d4d4301025440302c85006cf1614cb3f12cccccc01cf16c9ed54e03027c0058e235f06708018c8cb055004cf1623fa0213cb6acb1fcb3f820afaf08070fb02c98306fb00e0363705c0068e1a02fa403045501413c85006cf1614cb3f12cccccc01cf16c9ed54e05f06840ff2f0002d501c8cb3ff828cf16c97020c8cb0113f400f400cb00c980201200c0d001b3e401d3232c084b281f2fff27420003d16bc025c087c029de0063232c15633c594013e8084f2dac4b333325c7ec0200201201011003fbc82df6a2687d20699fa9906380e0004a187d2000ef00ea6a6a182a812f81ac40007b8b5d31802012012130201661415004db4f47da89a1f481a67ea6418e0380012861f48003bc03a9a9a860aa04204abe0be012e003e0150003caa15ed44d0fa40d33f5320c701c0009430fa4001de01d4d4d43055026c51004eaad7ed44d0fa40d33f5320c701c0009430fa4001de01d4d4d4305502155f05d0d30fd30ffa403001d8a761"  # noqa

    def __init__(
            self,
            owner_address: Address,
            next_item_index: int,
            content: Union[CollectionOnchainContent, CollectionOffchainContent],
            royalty_params: RoyaltyParams,
    ) -> None:
        self._data = self.create_data(owner_address, next_item_index, content, royalty_params).serialize()
        self._code = Cell.one_from_boc(self.CODE_HEX)

    @classmethod
    def create_data(
            cls,
            owner_address: Address,
            next_item_index: int,
            content: Union[CollectionOnchainContent, CollectionOffchainContent],
            royalty_params: RoyaltyParams,
    ) -> CollectionData:
        return CollectionData(
            owner_address=owner_address,
            next_item_index=next_item_index,
            content=content,
            royalty_params=royalty_params,
            nft_item_code=NFTEditable.CODE_HEX,
        )

    @classmethod
    def build_mint_body(
            cls,
            index: int,
            owner_address: Address,
            content: Union[NFTOnchainContent, NFTOffchainContent],
            editor_address: Optional[Address] = None,
            amount: int = 20000000,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the mint transaction.

        :param index: The index of the nft to be minted.
        :param content: The content of the nft to be minted.
        :param owner_address: The address of the owner.
        :param editor_address: The address of the editor. Defaults to the owner address.
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
                .store_address(editor_address or owner_address)
                .store_ref(content.serialize())
                .end_cell()
            )
            .end_cell()
        )

    @classmethod
    def build_batch_mint_body(
            cls,
            data: List[Tuple[Union[NFTOnchainContent, NFTOffchainContent], Address, Optional[Address]]],
            from_index: int,
            amount_per_one: int = 20000000,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the batch mint transaction.

        :param data: The list of data for minting. Each tuple contains:
            - OffchainCommonContent: The content of the nft to be minted.
            - Address: The address of the owner.
            - Optional[Address]: The address of the editor (if any) defaults to the owner address.
        :param from_index: The starting index for minting.
        :param amount_per_one: The amount of coins in nanoton per nft. Defaults to 20000000.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the batch mint transaction.
        """
        items_dict = HashMap(key_size=64)

        for i, (content, owner_address, editor_address) in enumerate(data, start=0):
            items_dict.set_int_key(
                i + from_index,
                begin_cell()
                .store_coins(amount_per_one)
                .store_ref(
                    begin_cell()
                    .store_address(owner_address)
                    .store_address(editor_address or owner_address)
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

    @classmethod
    def build_edit_content_body(
            cls,
            content: Union[CollectionOnchainContent, CollectionOffchainContent],
            royalty_params: RoyaltyParams,
            query_id: int = 0
    ) -> Cell:
        """
        Builds the body of the edit content transaction.

        :param content: The new content to be set.
        :param royalty_params: The new royalty parameters to be set.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the edit content transaction.
        """
        return (
            begin_cell()
            .store_uint(COLLECTION_EDIT_CONTENT_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_ref(content.serialize())
            .store_ref(royalty_params.serialize())
            .end_cell()
        )

    @classmethod
    def build_change_owner_body(
            cls,
            owner_address: Address,
            query_id: int = 0,
    ) -> Cell:
        """
        Builds the body of the change owner transaction.

        :param owner_address: The new owner address.
        :param query_id: The query ID. Defaults to 0.
        :return: The cell representing the body of the change owner transaction.
        """
        return (
            begin_cell()
            .store_uint(CHANGE_COLLECTION_OWNER_OPCODE, 32)
            .store_uint(query_id, 64)
            .store_address(owner_address)
            .end_cell()
        )
