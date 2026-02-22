from __future__ import annotations

import typing as t
from contextlib import suppress

from pytoniq_core import Builder, Cell, Slice, HashMap, TlbScheme, begin_cell

from tonutils.contracts.opcodes import OpCode
from tonutils.types import AddressLike, MetadataPrefix
from tonutils.utils import string_hash


class RoyaltyParams(TlbScheme):
    """Royalty parameters for NFT sales."""

    def __init__(
        self,
        royalty: int,
        denominator: int,
        address: AddressLike,
    ) -> None:
        """
        :param royalty: Royalty numerator.
        :param denominator: Royalty denominator.
        :param address: Royalty recipient address.
        """
        self.royalty = royalty
        self.denominator = denominator
        self.address = address

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `royalty:uint16 denominator:uint16 address:address`
        """
        cell = begin_cell()
        cell.store_uint(self.royalty, 16)
        cell.store_uint(self.denominator, 16)
        cell.store_address(self.address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> RoyaltyParams:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            royalty=cs.load_uint(16),
            denominator=cs.load_uint(16),
            address=cs.load_address(),
        )


class OnchainContent(TlbScheme):
    """On-chain NFT metadata stored directly in contract data."""

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
        """
        :param data: Metadata key-value pairs.
        """
        self.metadata = data

    @staticmethod
    def _value_serializer(val: t.Any, b: Builder) -> Builder:
        """Serialize a metadata value into a `Builder`.

        :param val: Value to serialize (string or `Cell`).
        :param b: Target builder.
        :return: The same builder.
        """
        if isinstance(val, str):
            cell = begin_cell()
            cell.store_uint(MetadataPrefix.ONCHAIN, 8)
            cell.store_snake_string(val)
            val = cell.end_cell()
        return b.store_ref(val)

    @staticmethod
    def _value_deserializer(val: Slice) -> t.Union[Cell, str]:
        """Deserialize a metadata value from a `Slice`.

        :param val: Source slice.
        :return: Decoded string or raw `Cell`.
        """
        with suppress(Exception):
            cs = val.copy().load_ref().begin_parse()
            cs.skip_bits(8)
            return cs.load_snake_string()
        return val.to_cell()

    def _build_hashmap(self) -> HashMap:
        """Build `HashMap` from metadata dictionary.

        :return: Serializable `HashMap`.
        """
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
        """Convert known integer keys to string keys.

        :param hashmap: Raw deserialized hashmap.
        :return: Parsed metadata dictionary.
        """
        for key in cls._KNOWN_KEYS:
            int_key = string_hash(key)
            if int_key in hashmap:
                hashmap[key] = hashmap[int_key]
                hashmap.pop(int_key)
        return hashmap

    def serialize(self, with_prefix: bool) -> Cell:
        """Serialize to `Cell`.

        TLB: `[prefix:uint8] metadata:dict`

        :param with_prefix: Include metadata prefix byte.
        """
        cell = begin_cell()
        if with_prefix:
            cell.store_uint(MetadataPrefix.ONCHAIN, 8)
        cell.store_dict(self._build_hashmap().serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice, with_prefix: bool) -> OnchainContent:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        :param with_prefix: Whether prefix byte is present.
        """
        if with_prefix:
            cs.skip_bits(8)
        data = cs.load_dict(
            key_length=256,
            value_deserializer=cls._value_deserializer,
        )
        return cls(cls._parse_hashmap(data))


class OffchainContent(TlbScheme):
    """Off-chain NFT metadata stored as URI reference."""

    def __init__(self, uri: str) -> None:
        """
        :param uri: URI to metadata JSON.
        """
        self.uri: str = uri

    def serialize(self, with_prefix: bool) -> Cell:
        """Serialize to `Cell`.

        TLB: `[prefix:uint8] uri:snake_string`

        :param with_prefix: Include metadata prefix byte.
        """
        cell = begin_cell()
        if with_prefix:
            cell.store_uint(MetadataPrefix.OFFCHAIN, 8)
        cell.store_snake_string(self.uri)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice, with_prefix: bool) -> OffchainContent:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        :param with_prefix: Whether prefix byte is present.
        """
        if with_prefix:
            cs.skip_bits(8)
        uri = cs.load_snake_string()
        return cls(uri=uri)


class OffchainCommonContent(TlbScheme):
    """Common base URI for off-chain item metadata in a collection."""

    def __init__(self, prefix_uri: str) -> None:
        """
        :param prefix_uri: Base URI prefix for all items.
        """
        self.prefix_uri = prefix_uri

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `prefix_uri:snake_string`
        """
        cell = begin_cell()
        cell.store_snake_string(self.prefix_uri)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> OffchainCommonContent:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        uri = cs.load_snake_string()
        return cls(prefix_uri=uri)


class OffchainItemContent(TlbScheme):
    """Per-item suffix for off-chain NFT metadata URI."""

    def __init__(self, suffix_uri: str) -> None:
        """
        :param suffix_uri: Item-specific URI suffix.
        """
        self.suffix_uri = suffix_uri

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `suffix_uri:snake_string`
        """
        cell = begin_cell()
        cell.store_snake_string(self.suffix_uri)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> OffchainItemContent:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        uri = cs.load_snake_string()
        return cls(suffix_uri=uri)


class NFTCollectionContent(TlbScheme):
    """Complete NFT collection metadata."""

    def __init__(
        self,
        content: t.Union[OnchainContent, OffchainContent],
        common_content: OffchainCommonContent,
    ) -> None:
        """
        :param content: Collection metadata (on-chain or off-chain).
        :param common_content: Common base URI for item metadata.
        """
        self.content = content
        self.common_content = common_content

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `content:^Cell common_content:^Cell`
        """
        cell = begin_cell()
        cell.store_ref(self.content.serialize(with_prefix=True))
        cell.store_ref(self.common_content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionContent:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
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
    """On-chain data for NFT collection contracts (TEP-62)."""

    def __init__(
        self,
        owner_address: AddressLike,
        content: NFTCollectionContent,
        royalty_params: RoyaltyParams,
        nft_item_code: Cell,
        next_item_index: int = 0,
    ) -> None:
        """
        :param owner_address: Collection owner address.
        :param content: Collection metadata.
        :param royalty_params: Royalty configuration.
        :param nft_item_code: Code cell for NFT item contracts.
        :param next_item_index: Next item index to mint.
        """
        self.owner_address = owner_address
        self.content = content
        self.royalty_params = royalty_params
        self.nft_item_code = nft_item_code
        self.next_item_index = next_item_index

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `owner:address next_item_index:uint64 content:^Cell
        nft_item_code:^Cell royalty_params:^Cell`
        """
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_uint(self.next_item_index, 64)
        cell.store_ref(self.content.serialize())
        cell.store_ref(self.nft_item_code)
        cell.store_ref(self.royalty_params.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionData:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            owner_address=cs.load_address(),
            next_item_index=cs.load_uint(64),
            content=NFTCollectionContent.deserialize(cs.load_ref().begin_parse()),
            nft_item_code=cs.load_ref(),
            royalty_params=RoyaltyParams.deserialize(cs.load_ref().begin_parse()),
        )


class NFTItemStandardData(TlbScheme):
    """On-chain data for standard NFT item contracts (TEP-62)."""

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OffchainItemContent,
    ) -> None:
        """
        :param index: Item index within collection.
        :param collection_address: Parent collection address.
        :param owner_address: Current owner address.
        :param content: Item metadata reference.
        """
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `index:uint64 collection:address owner:address content:^Cell`
        """
        cell = begin_cell()
        cell.store_uint(self.index, 64)
        cell.store_address(self.collection_address)
        cell.store_address(self.owner_address)
        cell.store_ref(self.content)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemStandardData:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            index=cs.load_uint(64),
            collection_address=cs.load_address(),
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
        )


class NFTItemEditableData(TlbScheme):
    """On-chain data for editable NFT item contracts (TEP-62)."""

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OffchainItemContent,
        editor_address: AddressLike,
    ) -> None:
        """
        :param index: Item index within collection.
        :param collection_address: Parent collection address.
        :param owner_address: Current owner address.
        :param content: Item metadata reference.
        :param editor_address: Address authorized to edit content.
        """
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content
        self.editor_address = editor_address

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `index:uint64 collection:address owner:address
        content:^Cell editor:address`
        """
        cell = begin_cell()
        cell.store_uint(self.index, 64)
        cell.store_address(self.collection_address)
        cell.store_address(self.owner_address)
        cell.store_ref(self.content)
        cell.store_address(self.editor_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemEditableData:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            index=cs.load_uint(64),
            collection_address=cs.load_address(),
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
            editor_address=cs.load_address(),
        )


class NFTItemSoulboundData(TlbScheme):
    """On-chain data for Soulbound Token contracts (TEP-85)."""

    def __init__(
        self,
        index: int,
        collection_address: AddressLike,
        owner_address: AddressLike,
        content: OffchainItemContent,
        authority_address: AddressLike,
        revoked_at: int = 0,
    ) -> None:
        """
        :param index: Item index within collection.
        :param collection_address: Parent collection address.
        :param owner_address: Current owner address.
        :param content: Item metadata reference.
        :param authority_address: Address authorized to revoke.
        :param revoked_at: Revocation unix timestamp, or 0.
        """
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content
        self.authority_address = authority_address
        self.revoked_at = revoked_at

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `index:uint64 collection:address owner:address content:^Cell
        authority:address revoked_at:uint64`
        """
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
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            index=cs.load_uint(64),
            collection_address=cs.load_address(),
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
            authority_address=cs.load_address(),
            revoked_at=cs.load_uint(64),
        )


class NFTItemStandardMintRef(TlbScheme):
    """Mint reference for standard NFT items."""

    def __init__(
        self,
        owner_address: AddressLike,
        content: OffchainItemContent,
    ) -> None:
        """
        :param owner_address: Initial owner address.
        :param content: Item metadata reference.
        """
        self.owner_address = owner_address
        self.content = content

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `owner:address content:^Cell`
        """
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemStandardMintRef:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
        )


class NFTItemEditableMintRef(TlbScheme):
    """Mint reference for editable NFT items."""

    def __init__(
        self,
        owner_address: AddressLike,
        editor_address: AddressLike,
        content: OffchainItemContent,
    ) -> None:
        """
        :param owner_address: Initial owner address.
        :param editor_address: Address authorized to edit content.
        :param content: Item metadata reference.
        """
        self.owner_address = owner_address
        self.editor_address = editor_address
        self.content = content

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `owner:address editor:address content:^Cell`
        """
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_address(self.editor_address)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemEditableMintRef:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            owner_address=cs.load_address(),
            editor_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
        )


class NFTItemSoulboundMintRef(TlbScheme):
    """Mint reference for Soulbound Tokens (SBTs)."""

    def __init__(
        self,
        owner_address: AddressLike,
        content: OffchainItemContent,
        authority_address: AddressLike,
        revoked_time: int = 0,
    ) -> None:
        """
        :param owner_address: Initial owner address.
        :param content: Item metadata reference.
        :param authority_address: Address authorized to revoke.
        :param revoked_time: Initial revocation timestamp.
        """
        self.owner_address = owner_address
        self.content = content
        self.authority_address = authority_address
        self.revoked_time = revoked_time

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `owner:address content:^Cell authority:address revoked_time:uint64`
        """
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_ref(self.content.serialize())
        cell.store_address(self.authority_address)
        cell.store_uint(self.revoked_time, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemSoulboundMintRef:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
            authority_address=cs.load_address(),
            revoked_time=cs.load_uint(64),
        )


class NFTCollectionMintItemBody(TlbScheme):
    """Message body for minting a single NFT item."""

    def __init__(
        self,
        item_index: int,
        item_ref: Cell,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        """
        :param item_index: Index for the new item.
        :param item_ref: Mint reference cell.
        :param forward_amount: Amount to forward in nanotons.
        :param query_id: Query identifier.
        """
        self.item_index = item_index
        self.item_ref = item_ref
        self.forward_amount = forward_amount
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 item_index:uint64
        forward_amount:coins item_ref:^Cell`
        """
        cell = begin_cell()
        cell.store_uint(1, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_uint(self.item_index, 64)
        cell.store_coins(self.forward_amount)
        cell.store_ref(self.item_ref)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionMintItemBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class NFTCollectionBatchMintItemBody(TlbScheme):
    """Message body for batch minting multiple NFT items."""

    MAX_BATCH_ITEMS = 249

    def __init__(
        self,
        items_refs: t.List[Cell],
        from_index: int,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        """
        :param items_refs: List of mint reference cells.
        :param from_index: Starting index for batch.
        :param forward_amount: Amount to forward per item in nanotons.
        :param query_id: Query identifier.
        :raises ValueError: If batch size exceeds `MAX_BATCH_ITEMS`.
        """
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
        """Parse hashmap of items from a `Slice`.

        :param cs: Source slice containing hashmap.
        :return: Sorted list of (index, amount, item_ref) tuples.
        """
        hashmap = cs.load_dict(key_length=64)
        out: t.List[tuple[int, int, Cell]] = []
        for key, val in hashmap.items():
            amount = val.load_coins()
            item_ref = val.load_ref()
            out.append((key, amount, item_ref))
        out.sort(key=lambda x: x[0])
        return out

    def _build_hashmap(self) -> HashMap:
        """Build `HashMap` from items list.

        :return: Serializable `HashMap`.
        """
        hashmap = HashMap(key_size=64)
        for key, item_ref in enumerate(self.items_refs, start=self.from_index):
            val = begin_cell()
            val.store_coins(self.forward_amount)
            val.store_ref(item_ref)
            hashmap.set_int_key(key, val.end_cell())
        return hashmap

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 items:dict`
        """
        cell = begin_cell()
        cell.store_uint(2, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_dict(self._build_hashmap().serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionBatchMintItemBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class NFTCollectionChangeOwnerBody(TlbScheme):
    """Message body for changing NFT collection owner."""

    def __init__(
        self,
        owner_address: AddressLike,
        query_id: int = 0,
    ) -> None:
        """
        :param owner_address: New owner address.
        :param query_id: Query identifier.
        """
        self.owner_address = owner_address
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 owner:address`
        """
        cell = begin_cell()
        cell.store_uint(3, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.owner_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionChangeOwnerBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class NFTCollectionChangeContentBody(TlbScheme):
    """Message body for changing NFT collection metadata."""

    def __init__(
        self,
        content: NFTCollectionContent,
        royalty_params: RoyaltyParams,
        query_id: int = 0,
    ) -> None:
        """
        :param content: New collection content.
        :param royalty_params: New royalty parameters.
        :param query_id: Query identifier.
        """
        self.content = content
        self.royalty_params = royalty_params
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 content:^Cell royalty_params:^Cell`
        """
        cell = begin_cell()
        cell.store_uint(4, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize())
        cell.store_ref(self.royalty_params.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionChangeContentBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class NFTEditContentBody(TlbScheme):
    """Message body for editing NFT item content."""

    def __init__(
        self,
        content: OffchainItemContent,
        query_id: int = 0,
    ) -> None:
        """
        :param content: New item content.
        :param query_id: Query identifier.
        """
        self.content = content
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 content:^Cell`
        """
        cell = begin_cell()
        cell.store_uint(OpCode.NFT_EDIT_CONTENT, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTEditContentBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class NFTTransferEditorshipBody(TlbScheme):
    """Message body for transferring NFT editorship rights."""

    def __init__(
        self,
        editor_address: AddressLike,
        response_address: AddressLike,
        custom_payload: t.Optional[Cell] = None,
        forward_payload: t.Optional[Cell] = None,
        forward_amount: int = 1,
        query_id: int = 0,
    ) -> None:
        """
        :param editor_address: New editor address.
        :param response_address: Address for excess funds.
        :param custom_payload: Custom payload cell, or `None`.
        :param forward_payload: Payload to forward, or `None`.
        :param forward_amount: Amount to forward in nanotons.
        :param query_id: Query identifier.
        """
        self.editor_address = editor_address
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 editor:address response:address
        custom_payload:^Cell forward_amount:coins forward_payload:^Cell`
        """
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
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class NFTDestroyBody(TlbScheme):
    """Message body for destroying a Soulbound Token."""

    def __init__(self, query_id: int = 0) -> None:
        """
        :param query_id: Query identifier.
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64`
        """
        cell = begin_cell()
        cell.store_uint(OpCode.SBT_DESTORY, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTDestroyBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class NFTRevokeBody(TlbScheme):
    """Message body for revoking a Soulbound Token."""

    def __init__(self, query_id: int = 0) -> None:
        """
        :param query_id: Query identifier.
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64`
        """
        cell = begin_cell()
        cell.store_uint(OpCode.SBT_REVOKE, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTRevokeBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError


class NFTTransferBody(TlbScheme):
    """Message body for transferring NFT ownership (TEP-62)."""

    def __init__(
        self,
        destination: AddressLike,
        response_address: t.Optional[AddressLike] = None,
        custom_payload: t.Optional[Cell] = None,
        forward_payload: t.Optional[Cell] = None,
        forward_amount: int = 1,
        query_id: int = 0,
    ) -> None:
        """
        :param destination: New owner address.
        :param response_address: Address for excess funds, or `None`.
        :param custom_payload: Custom payload cell, or `None`.
        :param forward_payload: Payload to forward, or `None`.
        :param forward_amount: Amount to forward in nanotons.
        :param query_id: Query identifier.
        """
        self.query_id = query_id
        self.destination = destination
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_amount = forward_amount
        self.forward_payload = forward_payload

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 query_id:uint64 destination:address response:address
        custom_payload:^Cell forward_amount:coins forward_payload:^Cell`
        """
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
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        raise NotImplementedError
