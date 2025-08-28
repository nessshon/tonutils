from __future__ import annotations

import typing as t

from pytoniq_core import (
    Cell,
    Slice,
    HashMap,
    TlbScheme,
    begin_cell,
)

from ...exceptions import UnexpectedOpCodeError
from ...types.common import AddressLike
from ...types.opcodes import OpCode
from ...types.tlb.content import (
    MetadataPrefix,
    OnchainContent,
    OffchainContent,
    OffchainItemContent,
    OffchainCommonContent,
)
from ...types.tlb.contract import BaseContractData


class RoyaltyParams(TlbScheme):

    def __init__(
        self,
        royalty: int,
        denominator: int,
        address: AddressLike,
    ) -> None:
        self.royalty = royalty
        self.denominator = denominator
        self.address = address

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.royalty, 16)
        cell.store_uint(self.denominator, 16)
        cell.store_address(self.address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> RoyaltyParams:
        return cls(
            royalty=cs.load_uint(16),
            denominator=cs.load_uint(16),
            address=cs.load_address(),
        )


class NFTCollectionContent(TlbScheme):

    def __init__(
        self,
        content: t.Union[OnchainContent, OffchainContent],
        common_content: OffchainCommonContent,
    ) -> None:
        self.content = content
        self.common_content = common_content

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_ref(self.content.serialize(with_prefix=True))
        cell.store_ref(self.common_content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionContent:
        content = cs.load_ref().begin_parse()
        prefix = MetadataPrefix(content.load_uint(8))
        if prefix == MetadataPrefix.ONCHAIN:
            content = OnchainContent.deserialize(content, False)
        else:
            content = OffchainContent.deserialize(content, False)
        common_content = OffchainCommonContent.deserialize(cs.load_ref().begin_parse())
        return cls(content=content, common_content=common_content)


class NFTCollectionData(BaseContractData):

    def __init__(
        self,
        owner_address: AddressLike,
        content: NFTCollectionContent,
        royalty_params: RoyaltyParams,
        nft_item_code: Cell,
        next_item_index: int = 0,
    ) -> None:
        super().__init__()
        self.owner_address = owner_address
        self.content = content
        self.royalty_params = royalty_params
        self.nft_item_code = nft_item_code
        self.next_item_index = next_item_index

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_uint(self.next_item_index, 64)
        cell.store_ref(self.content.serialize())
        cell.store_ref(self.nft_item_code)
        cell.store_ref(self.royalty_params.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionData:
        return cls(
            owner_address=cs.load_address(),
            next_item_index=cs.load_uint(64),
            content=NFTCollectionContent.deserialize(cs.load_ref().begin_parse()),
            nft_item_code=cs.load_ref(),
            royalty_params=RoyaltyParams.deserialize(cs.load_ref().begin_parse()),
        )


class NFTItemStandardData(BaseContractData):

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OffchainItemContent,
    ) -> None:
        super().__init__()
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.index, 64)
        cell.store_address(self.collection_address)
        cell.store_address(self.owner_address)
        cell.store_ref(self.content)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemStandardData:
        return cls(
            index=cs.load_uint(64),
            collection_address=cs.load_address(),
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
        )


class NFTItemEditableData(BaseContractData):

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OffchainItemContent,
        editor_address: AddressLike,
    ) -> None:
        super().__init__()
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content
        self.editor_address = editor_address

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.index, 64)
        cell.store_address(self.collection_address)
        cell.store_address(self.owner_address)
        cell.store_ref(self.content)
        cell.store_address(self.editor_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemEditableData:
        return cls(
            index=cs.load_uint(64),
            collection_address=cs.load_address(),
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
            editor_address=cs.load_address(),
        )


class NFTItemSoulboundData(BaseContractData):

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OffchainItemContent,
        authority_address: AddressLike,
        revoked_at: int = 0,
    ) -> None:
        super().__init__()
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content
        self.authority_address = authority_address
        self.revoked_at = revoked_at

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.index, 64)
        cell.store_address(self.collection_address)
        cell.store_address(self.owner_address)
        cell.store_ref(self.content)
        cell.store_address(self.authority_address)
        cell.store_uint(self.revoked_at, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemSoulboundData:
        return cls(
            index=cs.load_uint(64),
            collection_address=cs.load_address(),
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
            authority_address=cs.load_address(),
            revoked_at=cs.load_uint(64),
        )


class NFTItemStandardMintRef(TlbScheme):

    def __init__(
        self,
        owner_address: AddressLike,
        content: OffchainItemContent,
    ) -> None:
        self.owner_address = owner_address
        self.content = content

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemStandardMintRef:
        return cls(
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
        )


class NFTItemEditableMintRef(TlbScheme):

    def __init__(
        self,
        owner_address: AddressLike,
        editor_address: AddressLike,
        content: OffchainItemContent,
    ) -> None:
        self.owner_address = owner_address
        self.editor_address = editor_address
        self.content = content

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_address(self.editor_address)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemEditableMintRef:
        return cls(
            owner_address=cs.load_address(),
            editor_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
        )


class NFTItemSoulboundMintRef(TlbScheme):

    def __init__(
        self,
        owner_address: AddressLike,
        content: OffchainItemContent,
        authority_address: AddressLike,
        revoked_time: int = 0,
    ) -> None:
        self.owner_address = owner_address
        self.content = content
        self.authority_address = authority_address
        self.revoked_time = revoked_time

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_ref(self.content.serialize())
        cell.store_address(self.authority_address)
        cell.store_uint(self.revoked_time, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemSoulboundMintRef:
        return cls(
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
            authority_address=cs.load_address(),
            revoked_time=cs.load_uint(64),
        )


class NFTCollectionMintItem(TlbScheme):
    OP_CODE = 1

    def __init__(
        self,
        item_index: int,
        item_ref: Cell,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        self.item_index = item_index
        self.item_ref = item_ref
        self.forward_amount = forward_amount
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.OP_CODE, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_uint(self.item_index, 64)
        cell.store_coins(self.forward_amount)
        cell.store_ref(self.item_ref)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionMintItem:
        op_code = cs.load_uint(32)
        if op_code == cls.OP_CODE:
            return cls(
                query_id=cs.load_uint(64),
                item_index=cs.load_uint(64),
                forward_amount=cs.load_coins(),
                item_ref=cs.load_ref(),
            )
        raise UnexpectedOpCodeError(cls, cls.OP_CODE, op_code)


class NFTCollectionBatchMintItem(TlbScheme):
    OP_CODE = 2

    def __init__(
        self,
        items_refs: t.List[Cell],
        from_index: int,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        self.items_refs = items_refs
        self.from_index = from_index
        self.forward_amount = forward_amount
        self.query_id = query_id

    @classmethod
    def _parse_hashmap(cls, cs: Slice) -> t.List[t.Tuple[int, int, Cell]]:
        hashmap = cs.load_dict(key_length=64)
        out: list[tuple[int, int, Cell]] = []
        for key, val in hashmap.items():
            amount = val.load_coins()
            item_ref = val.load_ref()
            out.append((key, amount, item_ref))
        out.sort(key=lambda x: x[0])
        return out

    def _build_hashmap(self) -> HashMap:
        hashmap = HashMap(key_size=64)
        for key, item_ref in enumerate(self.items_refs, start=self.from_index):
            val = begin_cell()
            val.store_coins(self.forward_amount)
            val.store_ref(item_ref)
            hashmap.set_int_key(key, val.end_cell())
        return hashmap

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.OP_CODE, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_dict(self._build_hashmap().serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionBatchMintItem:
        op_code = cs.load_uint(32)
        if op_code == cls.OP_CODE:
            query_id = cs.load_uint(64)
            data = cls._parse_hashmap(cs)
            return cls(
                query_id=query_id,
                from_index=data[0][0],
                forward_amount=data[0][1],
                items_refs=[ref for _, _, ref in data],
            )
        raise UnexpectedOpCodeError(cls, cls.OP_CODE, op_code)


class NFTCollectionEditableChangeOwner(TlbScheme):
    OP_CODE = 3

    def __init__(
        self,
        owner_address: AddressLike,
        query_id: int = 0,
    ) -> None:
        self.owner_address = owner_address
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.OP_CODE, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.owner_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionEditableChangeOwner:
        op_code = cs.load_uint(32)
        if op_code == cls.OP_CODE:
            return cls(
                query_id=cs.load_uint(64),
                owner_address=cs.load_address(),
            )
        raise UnexpectedOpCodeError(cls, cls.OP_CODE, op_code)


class NFTCollectionEditableChangeContent(TlbScheme):
    OP_CODE = 4

    def __init__(
        self,
        content: NFTCollectionContent,
        royalty_params: RoyaltyParams,
        query_id: int = 0,
    ) -> None:
        self.content = content
        self.royalty_params = royalty_params
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.OP_CODE, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize())
        cell.store_ref(self.royalty_params.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionEditableChangeContent:
        op_code = cs.load_uint(32)
        if op_code == cls.OP_CODE:
            return cls(
                query_id=cs.load_uint(64),
                content=NFTCollectionContent.deserialize(cs.load_ref().begin_parse()),
                royalty_params=RoyaltyParams.deserialize(cs.load_ref().begin_parse()),
            )
        raise UnexpectedOpCodeError(cls, cls.OP_CODE, op_code)


class NFTItemEditableEditContent(TlbScheme):
    OP_CODE = OpCode.NFT_ITEM_EDIT_CONTENT

    def __init__(
        self,
        content: OffchainItemContent,
        query_id: int = 0,
    ) -> None:
        self.content = content
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.OP_CODE, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemEditableEditContent:
        op_code = cs.load_uint(32)
        if op_code == cls.OP_CODE:
            return cls(
                query_id=cs.load_uint(64),
                content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
            )
        raise UnexpectedOpCodeError(cls, cls.OP_CODE, op_code)


class NFTItemEditableTransferEditorship(TlbScheme):
    OP_CODE = OpCode.NFT_ITEM_TRANSFER_EDITORSHIP

    def __init__(
        self,
        editor_address: AddressLike,
        response_address: AddressLike,
        custom_payload: t.Optional[Cell] = None,
        forward_payload: t.Optional[Cell] = None,
        forward_amount: int = 1,
        query_id: int = 0,
    ) -> None:
        self.editor_address = editor_address
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.query_id = query_id

    def serialize(self, cs: Slice) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.OP_CODE, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.editor_address)
        cell.store_address(self.response_address)
        cell.store_maybe_ref(self.custom_payload)
        cell.store_coins(self.forward_amount)
        cell.store_maybe_ref(self.forward_payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemEditableTransferEditorship:
        op_code = cs.load_uint(32)
        if op_code == cls.OP_CODE:
            return cls(
                query_id=cs.load_uint(64),
                editor_address=cs.load_address(),
                response_address=cs.load_address(),
                custom_payload=cs.load_maybe_ref(),
                forward_amount=cs.load_coins(),
                forward_payload=cs.load_maybe_ref(),
            )
        raise UnexpectedOpCodeError(cls, cls.OP_CODE, op_code)


class NFTItemSoulboundDestory(TlbScheme):
    OP_CODE = OpCode.NFT_ITEM_DESTORY

    def __init__(self, query_id: int = 0) -> None:
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.OP_CODE, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemSoulboundDestory:
        op_code = cs.load_uint(32)
        if op_code == cls.OP_CODE:
            return cls(query_id=cs.load_uint(64))
        raise UnexpectedOpCodeError(cls, cls.OP_CODE, op_code)


class NFTItemSoulboundRevoke(TlbScheme):
    OP_CODE = OpCode.NFT_ITEM_REVOKE

    def __init__(self, query_id: int = 0) -> None:
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.OP_CODE, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemSoulboundRevoke:
        op_code = cs.load_uint(32)
        if op_code == cls.OP_CODE:
            return cls(query_id=cs.load_uint(64))
        raise UnexpectedOpCodeError(cls, cls.OP_CODE, op_code)


class NFTItemTransfer(TlbScheme):
    OP_CODE = OpCode.NFT_ITEM_TRANSFER

    def __init__(
        self,
        owner_address: AddressLike,
        response_address: t.Optional[AddressLike] = None,
        custom_payload: t.Optional[Cell] = None,
        forward_payload: t.Optional[Cell] = None,
        forward_amount: int = 1,
        query_id: int = 0,
    ) -> None:
        self.owner_address = owner_address
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(self.OP_CODE, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.owner_address)
        cell.store_address(self.response_address or self.owner_address)
        cell.store_maybe_ref(self.custom_payload)
        cell.store_coins(self.forward_amount)
        cell.store_maybe_ref(self.forward_payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemTransfer:
        op_code = cs.load_uint(32)
        if op_code == cls.OP_CODE:
            return cls(
                query_id=cs.load_uint(64),
                owner_address=cs.load_address(),
                response_address=cs.load_address(),
                custom_payload=cs.load_maybe_ref(),
                forward_amount=cs.load_coins(),
                forward_payload=cs.load_maybe_ref(),
            )
        raise UnexpectedOpCodeError(cls, cls.OP_CODE, op_code)
