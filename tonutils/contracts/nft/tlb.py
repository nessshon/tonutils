from __future__ import annotations

import typing as t
from contextlib import suppress

from pytoniq_core import Builder, Cell, Slice, HashMap, TlbScheme, begin_cell

from tonutils.contracts.opcodes import OpCode
from tonutils.types import AddressLike, MetadataPrefix
from tonutils.utils import string_hash


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


class OnchainContent(TlbScheme):
    _KNOWN_KEYS: t.Set[str] = {
        "uri",
        "name",
        "image",
        "image_data",
        "cover_image",
        "cover_image_data",
        "amount_style",
        "description",
        "decimals",
        "symbol",
    }

    def __init__(self, data: t.Dict[t.Union[str, int], t.Any]) -> None:
        self.metadata = data

    @staticmethod
    def _value_serializer(val: t.Any, b: Builder) -> Builder:
        if isinstance(val, str):
            cell = begin_cell()
            cell.store_uint(MetadataPrefix.ONCHAIN, 8)
            cell.store_snake_string(val)
            val = cell.end_cell()
        return b.store_ref(val)

    @staticmethod
    def _value_deserializer(val: Slice) -> t.Union[Cell, str]:
        with suppress(Exception):
            cs = val.copy().load_ref().begin_parse()
            cs.skip_bits(8)
            return cs.load_snake_string()
        return val.to_cell()

    def _build_hashmap(self) -> HashMap:
        hashmap = HashMap(
            key_size=256,
            value_serializer=self._value_serializer,
        )
        for key, val in self.metadata.items():
            if isinstance(key, str):
                key = string_hash(key)
            hashmap.set_int_key(key, val)
        return hashmap

    @classmethod
    def _parse_hashmap(
        cls,
        hashmap: t.Dict[t.Union[str, int], Cell],
    ) -> t.Dict[t.Union[str, int], t.Any]:
        for key in cls._KNOWN_KEYS:
            int_key = string_hash(key)
            if int_key in hashmap:
                hashmap[key] = hashmap[int_key]
                hashmap.pop(int_key)
        return hashmap

    def serialize(self, with_prefix: bool) -> Cell:
        cell = begin_cell()
        if with_prefix:
            cell.store_uint(MetadataPrefix.ONCHAIN, 8)
        cell.store_dict(self._build_hashmap().serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice, with_prefix: bool) -> OnchainContent:
        if with_prefix:
            cs.skip_bits(8)
        data = cs.load_dict(
            key_length=256,
            value_deserializer=cls._value_deserializer,
        )
        return cls(cls._parse_hashmap(data))


class OffchainContent(TlbScheme):

    def __init__(self, uri: str) -> None:
        self.uri: str = uri

    @classmethod
    def deserialize(cls, cs: Slice, with_prefix: bool) -> OffchainContent:
        if with_prefix:
            cs.skip_bits(8)
        uri = cs.load_snake_string()
        return cls(uri=uri)

    def serialize(self, with_prefix: bool) -> Cell:
        cell = begin_cell()
        if with_prefix:
            cell.store_uint(MetadataPrefix.OFFCHAIN, 8)
        cell.store_snake_string(self.uri)
        return cell.end_cell()


class OffchainCommonContent(TlbScheme):

    def __init__(self, suffix_uri: str) -> None:
        self.suffix_uri = suffix_uri

    @classmethod
    def deserialize(cls, cs: Slice) -> OffchainCommonContent:
        uri = cs.load_snake_string()
        return cls(suffix_uri=uri)

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_snake_string(self.suffix_uri)
        return cell.end_cell()


class OffchainItemContent(TlbScheme):

    def __init__(self, prefix_uri: str) -> None:
        self.prefix_uri = prefix_uri

    @classmethod
    def deserialize(cls, cs: Slice) -> OffchainItemContent:
        uri = cs.load_snake_string()
        return cls(prefix_uri=uri)

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_snake_string(self.prefix_uri)
        return cell.end_cell()


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
        return cls(
            content=(
                OnchainContent.deserialize(content, False)
                if MetadataPrefix(content.load_uint(8)) == MetadataPrefix.ONCHAIN
                else OffchainContent.deserialize(content, False)
            ),
            common_content=OffchainCommonContent.deserialize(
                cs.load_ref().begin_parse()
            ),
        )


class NFTCollectionData(TlbScheme):

    def __init__(
        self,
        owner_address: AddressLike,
        content: NFTCollectionContent,
        royalty_params: RoyaltyParams,
        nft_item_code: Cell,
        next_item_index: int = 0,
    ) -> None:
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


class NFTItemStandardData(TlbScheme):

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OffchainItemContent,
    ) -> None:
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


class NFTItemEditableData(TlbScheme):

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OffchainItemContent,
        editor_address: AddressLike,
    ) -> None:
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


class NFTItemSoulboundData(TlbScheme):

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OffchainItemContent,
        authority_address: AddressLike,
        revoked_at: int = 0,
    ) -> None:
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


class NFTCollectionMintItemBody(TlbScheme):

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
        cell.store_uint(1, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_uint(self.item_index, 64)
        cell.store_coins(self.forward_amount)
        cell.store_ref(self.item_ref)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionMintItemBody:
        raise NotImplementedError()


class NFTCollectionBatchMintItemBody(TlbScheme):
    MAX_BATCH_ITEMS = 249

    def __init__(
        self,
        items_refs: t.List[Cell],
        from_index: int,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        n = len(items_refs)
        if n > self.MAX_BATCH_ITEMS:
            raise ValueError(
                f"Batch mint limit exceeded: got {n} items, "
                f"but maximum allowed is {self.MAX_BATCH_ITEMS}."
            )

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
        cell.store_uint(2, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_dict(self._build_hashmap().serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionBatchMintItemBody:
        raise NotImplementedError()


class NFTCollectionChangeOwnerBody(TlbScheme):

    def __init__(
        self,
        owner_address: AddressLike,
        query_id: int = 0,
    ) -> None:
        self.owner_address = owner_address
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(3, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.owner_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionChangeOwnerBody:
        raise NotImplementedError()


class NFTCollectionChangeContentBody(TlbScheme):

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
        cell.store_uint(4, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize())
        cell.store_ref(self.royalty_params.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionChangeContentBody:
        raise NotImplementedError()


class NFTEditContentBody(TlbScheme):

    def __init__(
        self,
        content: OffchainItemContent,
        query_id: int = 0,
    ) -> None:
        self.content = content
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.NFT_EDIT_CONTENT, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTEditContentBody:
        raise NotImplementedError()


class NFTTransferEditorshipBody(TlbScheme):

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

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.NFT_TRANSFER_EDITORSHIP, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.editor_address)
        cell.store_address(self.response_address)
        cell.store_maybe_ref(self.custom_payload)
        cell.store_coins(self.forward_amount)
        cell.store_maybe_ref(self.forward_payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTTransferEditorshipBody:
        raise NotImplementedError()


class NFTDestroyBody(TlbScheme):

    def __init__(self, query_id: int = 0) -> None:
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.SBT_DESTORY, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTDestroyBody:
        raise NotImplementedError()


class NFTRevokeBody(TlbScheme):

    def __init__(self, query_id: int = 0) -> None:
        self.query_id = query_id

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.SBT_REVOKE, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTRevokeBody:
        raise NotImplementedError()


class NFTTransferBody(TlbScheme):

    def __init__(
        self,
        destination: AddressLike,
        response_address: t.Optional[AddressLike] = None,
        custom_payload: t.Optional[Cell] = None,
        forward_payload: t.Optional[Cell] = None,
        forward_amount: int = 1,
        query_id: int = 0,
    ) -> None:
        self.query_id = query_id
        self.destination = destination
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_amount = forward_amount
        self.forward_payload = forward_payload

    def serialize(self) -> Cell:
        cell = begin_cell()
        cell.store_uint(OpCode.NFT_TRANSFER, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.destination)
        cell.store_address(self.response_address)
        cell.store_maybe_ref(self.custom_payload)
        cell.store_coins(self.forward_amount)
        cell.store_maybe_ref(self.forward_payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTTransferBody:
        raise NotImplementedError
