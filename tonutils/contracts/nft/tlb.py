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
        Initialize royalty parameters.

        :param royalty: Royalty numerator (e.g., 5 for 5%)
        :param denominator: Royalty denominator (e.g., 100 for percentage)
        :param address: Address to receive royalty payments
        """
        self.royalty = royalty
        self.denominator = denominator
        self.address = address

    def serialize(self) -> Cell:
        """
        Serialize royalty params to Cell.

        Layout: royalty:uint16 denominator:uint16 address:address

        :return: Serialized royalty params cell
        """
        cell = begin_cell()
        cell.store_uint(self.royalty, 16)
        cell.store_uint(self.denominator, 16)
        cell.store_address(self.address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> RoyaltyParams:
        """
        Deserialize royalty params from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized RoyaltyParams instance
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
    """Set of recognized metadata keys."""

    def __init__(self, data: t.Dict[t.Union[str, int], t.Any]) -> None:
        """
        Initialize on-chain content.

        :param data: Dictionary of metadata key-value pairs
        """
        self.metadata = data

    @staticmethod
    def _value_serializer(val: t.Any, b: Builder) -> Builder:
        """
        Serialize metadata value to builder.

        :param val: Value to serialize (string or Cell)
        :param b: Builder to store to
        :return: Builder with stored value
        """
        if isinstance(val, str):
            cell = begin_cell()
            cell.store_uint(MetadataPrefix.ONCHAIN, 8)
            cell.store_snake_string(val)
            val = cell.end_cell()
        return b.store_ref(val)

    @staticmethod
    def _value_deserializer(val: Slice) -> t.Union[Cell, str]:
        """
        Deserialize metadata value from slice.

        :param val: Slice containing value
        :return: Deserialized string or Cell
        """
        with suppress(Exception):
            cs = val.copy().load_ref().begin_parse()
            cs.skip_bits(8)
            return cs.load_snake_string()
        return val.to_cell()

    def _build_hashmap(self) -> HashMap:
        """
        Build hashmap from metadata dictionary.

        :return: HashMap with serialized metadata
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
        """
        Parse hashmap and convert known integer keys to string keys.

        :param hashmap: Raw hashmap from deserialization
        :return: Parsed metadata dictionary
        """
        for key in cls._KNOWN_KEYS:
            int_key = string_hash(key)
            if int_key in hashmap:
                hashmap[key] = hashmap[int_key]
                hashmap.pop(int_key)
        return hashmap

    def serialize(self, with_prefix: bool) -> Cell:
        """
        Serialize on-chain content to Cell.

        Layout: [prefix:uint8] metadata:dict

        :param with_prefix: Whether to include metadata prefix byte
        :return: Serialized content cell
        """
        cell = begin_cell()
        if with_prefix:
            cell.store_uint(MetadataPrefix.ONCHAIN, 8)
        cell.store_dict(self._build_hashmap().serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice, with_prefix: bool) -> OnchainContent:
        """
        Deserialize on-chain content from Cell slice.

        :param cs: Cell slice to deserialize from
        :param with_prefix: Whether prefix byte is present
        :return: Deserialized OnchainContent instance
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
        Initialize off-chain content.

        :param uri: URI to metadata JSON (e.g., "https://...")
        """
        self.uri: str = uri

    def serialize(self, with_prefix: bool) -> Cell:
        """
        Serialize off-chain content to Cell.

        Layout: [prefix:uint8] uri:snake_string

        :param with_prefix: Whether to include metadata prefix byte
        :return: Serialized content cell
        """
        cell = begin_cell()
        if with_prefix:
            cell.store_uint(MetadataPrefix.OFFCHAIN, 8)
        cell.store_snake_string(self.uri)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice, with_prefix: bool) -> OffchainContent:
        """
        Deserialize off-chain content from Cell slice.

        :param cs: Cell slice to deserialize from
        :param with_prefix: Whether prefix byte is present
        :return: Deserialized OffchainContent instance
        """
        if with_prefix:
            cs.skip_bits(8)
        uri = cs.load_snake_string()
        return cls(uri=uri)


class OffchainCommonContent(TlbScheme):
    """Common base URI for off-chain item metadata in a collection."""

    def __init__(self, prefix_uri: str) -> None:
        """
        Initialize common item metadata base URI.

        :param prefix_uri: Base URI prefix for all items (e.g., "https://example.com/items/")
        """
        self.prefix_uri = prefix_uri

    def serialize(self) -> Cell:
        """
        Serialize common content to Cell.

        Layout: prefix_uri:snake_string

        :return: Serialized content cell
        """
        cell = begin_cell()
        cell.store_snake_string(self.prefix_uri)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> OffchainCommonContent:
        """
        Deserialize common content from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized OffchainCommonContent instance
        """
        uri = cs.load_snake_string()
        return cls(prefix_uri=uri)


class OffchainItemContent(TlbScheme):
    """Per-item suffix for off-chain NFT metadata URI."""

    def __init__(self, suffix_uri: str) -> None:
        """
        Initialize item metadata suffix.

        :param suffix_uri: Item-specific URI suffix (e.g., "0.json" for item #0)
        """
        self.suffix_uri = suffix_uri

    def serialize(self) -> Cell:
        """
        Serialize item content to Cell.

        Layout: suffix_uri:snake_string

        :return: Serialized content cell
        """
        cell = begin_cell()
        cell.store_snake_string(self.suffix_uri)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> OffchainItemContent:
        """
        Deserialize item content from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized OffchainItemContent instance
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
        Initialize collection content.

        :param content: Collection metadata (on-chain or off-chain)
        :param common_content: Common base URI for item metadata (used as prefix for all item content)
        """
        self.content = content
        self.common_content = common_content

    def serialize(self) -> Cell:
        """
        Serialize collection content to Cell.

        Layout: content:^Cell common_content:^Cell

        :return: Serialized content cell
        """
        cell = begin_cell()
        cell.store_ref(self.content.serialize(with_prefix=True))
        cell.store_ref(self.common_content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionContent:
        """
        Deserialize collection content from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTCollectionContent instance
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
        Initialize collection data.

        :param owner_address: Collection owner address
        :param content: Collection metadata
        :param royalty_params: Royalty configuration for all items
        :param nft_item_code: Code cell for NFT item contracts
        :param next_item_index: Next item index to mint (default: 0)
        """
        self.owner_address = owner_address
        self.content = content
        self.royalty_params = royalty_params
        self.nft_item_code = nft_item_code
        self.next_item_index = next_item_index

    def serialize(self) -> Cell:
        """
        Serialize collection data to Cell.

        Layout: owner:address next_item_index:uint64 content:^Cell
                nft_item_code:^Cell royalty_params:^Cell

        :return: Serialized data cell
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
        """
        Deserialize collection data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTCollectionData instance
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
        Initialize standard NFT item data.

        :param index: Item index within collection
        :param collection_address: Parent collection address
        :param owner_address: Current owner address
        :param content: Item metadata reference
        """
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content

    def serialize(self) -> Cell:
        """
        Serialize item data to Cell.

        Layout: index:uint64 collection:address owner:address content:^Cell

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_uint(self.index, 64)
        cell.store_address(self.collection_address)
        cell.store_address(self.owner_address)
        cell.store_ref(self.content)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemStandardData:
        """
        Deserialize item data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTItemStandardData instance
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
        Initialize editable NFT item data.

        :param index: Item index within collection
        :param collection_address: Parent collection address
        :param owner_address: Current owner address
        :param content: Item metadata reference
        :param editor_address: Address authorized to edit content
        """
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content
        self.editor_address = editor_address

    def serialize(self) -> Cell:
        """
        Serialize item data to Cell.

        Layout: index:uint64 collection:address owner:address
                content:^Cell editor:address

        :return: Serialized data cell
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
        """
        Deserialize item data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTItemEditableData instance
        """
        return cls(
            index=cs.load_uint(64),
            collection_address=cs.load_address(),
            owner_address=cs.load_address(),
            content=OffchainItemContent.deserialize(cs.load_ref().begin_parse()),
            editor_address=cs.load_address(),
        )


class NFTItemSoulboundData(TlbScheme):
    """On-chain data for Soulbound Token (SBT) contracts (TEP-85)."""

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
        Initialize soulbound token data.

        :param index: Item index within collection
        :param collection_address: Parent collection address
        :param owner_address: Current owner address (cannot transfer)
        :param content: Item metadata reference
        :param authority_address: Address authorized to revoke token
        :param revoked_at: Unix timestamp of revocation (0 if not revoked)
        """
        self.index = index
        self.collection_address = collection_address
        self.owner_address = owner_address
        self.content = content
        self.authority_address = authority_address
        self.revoked_at = revoked_at

    def serialize(self) -> Cell:
        """
        Serialize SBT data to Cell.

        Layout: index:uint64 collection:address owner:address content:^Cell
                authority:address revoked_at:uint64

        :return: Serialized data cell
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
        """
        Deserialize SBT data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTItemSoulboundData instance
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
        Initialize standard mint reference.

        :param owner_address: Initial owner address
        :param content: Item metadata reference
        """
        self.owner_address = owner_address
        self.content = content

    def serialize(self) -> Cell:
        """
        Serialize mint reference to Cell.

        Layout: owner:address content:^Cell

        :return: Serialized mint ref cell
        """
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemStandardMintRef:
        """
        Deserialize mint reference from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTItemStandardMintRef instance
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
        Initialize editable mint reference.

        :param owner_address: Initial owner address
        :param editor_address: Address authorized to edit content
        :param content: Item metadata reference
        """
        self.owner_address = owner_address
        self.editor_address = editor_address
        self.content = content

    def serialize(self) -> Cell:
        """
        Serialize mint reference to Cell.

        Layout: owner:address editor:address content:^Cell

        :return: Serialized mint ref cell
        """
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_address(self.editor_address)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemEditableMintRef:
        """
        Deserialize mint reference from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTItemEditableMintRef instance
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
        Initialize soulbound mint reference.

        :param owner_address: Initial owner address
        :param content: Item metadata reference
        :param authority_address: Address authorized to revoke token
        :param revoked_time: Initial revocation timestamp (default: 0)
        """
        self.owner_address = owner_address
        self.content = content
        self.authority_address = authority_address
        self.revoked_time = revoked_time

    def serialize(self) -> Cell:
        """
        Serialize mint reference to Cell.

        Layout: owner:address content:^Cell authority:address revoked_time:uint64

        :return: Serialized mint ref cell
        """
        cell = begin_cell()
        cell.store_address(self.owner_address)
        cell.store_ref(self.content.serialize())
        cell.store_address(self.authority_address)
        cell.store_uint(self.revoked_time, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTItemSoulboundMintRef:
        """
        Deserialize mint reference from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTItemSoulboundMintRef instance
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
        Initialize mint item message body.

        :param item_index: Index for the new item
        :param item_ref: Mint reference cell (owner, content, etc.)
        :param forward_amount: Amount to forward to item contract in nanotons
        :param query_id: Query identifier (default: 0)
        """
        self.item_index = item_index
        self.item_ref = item_ref
        self.forward_amount = forward_amount
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize mint body to Cell.

        Layout: op_code:uint32 query_id:uint64 item_index:uint64
                forward_amount:coins item_ref:^Cell

        :return: Serialized message body cell
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
        """
        Deserialize mint body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTCollectionMintItemBody instance
        """
        raise NotImplementedError


class NFTCollectionBatchMintItemBody(TlbScheme):
    """Message body for batch minting multiple NFT items."""

    MAX_BATCH_ITEMS = 249
    """Maximum number of items allowed in a single batch mint."""

    def __init__(
        self,
        items_refs: t.List[Cell],
        from_index: int,
        forward_amount: int,
        query_id: int = 0,
    ) -> None:
        """
        Initialize batch mint message body.

        :param items_refs: List of mint reference cells
        :param from_index: Starting index for batch
        :param forward_amount: Amount to forward per item in nanotons
        :param query_id: Query identifier (default: 0)
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
        """
        Parse hashmap of items from slice.

        :param cs: Cell slice containing hashmap
        :return: Sorted list of (index, amount, item_ref) tuples
        """
        hashmap = cs.load_dict(key_length=64)
        out: list[tuple[int, int, Cell]] = []
        for key, val in hashmap.items():
            amount = val.load_coins()
            item_ref = val.load_ref()
            out.append((key, amount, item_ref))
        out.sort(key=lambda x: x[0])
        return out

    def _build_hashmap(self) -> HashMap:
        """
        Build hashmap from items list.

        :return: HashMap with item indices and references
        """
        hashmap = HashMap(key_size=64)
        for key, item_ref in enumerate(self.items_refs, start=self.from_index):
            val = begin_cell()
            val.store_coins(self.forward_amount)
            val.store_ref(item_ref)
            hashmap.set_int_key(key, val.end_cell())
        return hashmap

    def serialize(self) -> Cell:
        """
        Serialize batch mint body to Cell.

        Layout: op_code:uint32 query_id:uint64 items:dict

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(2, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_dict(self._build_hashmap().serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionBatchMintItemBody:
        """
        Deserialize batch mint body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTCollectionBatchMintItemBody instance
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
        Initialize change owner message body.

        :param owner_address: New owner address
        :param query_id: Query identifier (default: 0)
        """
        self.owner_address = owner_address
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize change owner body to Cell.

        Layout: op_code:uint32 query_id:uint64 owner:address

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(3, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_address(self.owner_address)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionChangeOwnerBody:
        """
        Deserialize change owner body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTCollectionChangeOwnerBody instance
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
        Initialize change content message body.

        :param content: New collection content
        :param royalty_params: New royalty parameters
        :param query_id: Query identifier (default: 0)
        """
        self.content = content
        self.royalty_params = royalty_params
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize change content body to Cell.

        Layout: op_code:uint32 query_id:uint64 content:^Cell royalty_params:^Cell

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(4, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize())
        cell.store_ref(self.royalty_params.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTCollectionChangeContentBody:
        """
        Deserialize change content body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTCollectionChangeContentBody instance
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
        Initialize edit content message body.

        :param content: New item content
        :param query_id: Query identifier (default: 0)
        """
        self.content = content
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize edit content body to Cell.

        Layout: op_code:uint32 query_id:uint64 content:^Cell

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.NFT_EDIT_CONTENT, 32)
        cell.store_uint(self.query_id, 64)
        cell.store_ref(self.content.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTEditContentBody:
        """
        Deserialize edit content body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTEditContentBody instance
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
        Initialize transfer editorship message body.

        :param editor_address: New editor address
        :param response_address: Address for excess funds
        :param custom_payload: Optional custom payload cell
        :param forward_payload: Optional payload to forward
        :param forward_amount: Amount to forward in nanotons (default: 1)
        :param query_id: Query identifier (default: 0)
        """
        self.editor_address = editor_address
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize transfer editorship body to Cell.

        Layout: op_code:uint32 query_id:uint64 editor:address response:address
                custom_payload:^Cell forward_amount:coins forward_payload:^Cell

        :return: Serialized message body cell
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
        """
        Deserialize transfer editorship body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTTransferEditorshipBody instance
        """
        raise NotImplementedError


class NFTDestroyBody(TlbScheme):
    """Message body for destroying a Soulbound Token."""

    def __init__(self, query_id: int = 0) -> None:
        """
        Initialize destroy message body.

        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize destroy body to Cell.

        Layout: op_code:uint32 query_id:uint64

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.SBT_DESTORY, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTDestroyBody:
        """
        Deserialize destroy body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTDestroyBody instance
        """
        raise NotImplementedError


class NFTRevokeBody(TlbScheme):
    """Message body for revoking a Soulbound Token."""

    def __init__(self, query_id: int = 0) -> None:
        """
        Initialize revoke message body.

        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id

    def serialize(self) -> Cell:
        """
        Serialize revoke body to Cell.

        Layout: op_code:uint32 query_id:uint64

        :return: Serialized message body cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.SBT_REVOKE, 32)
        cell.store_uint(self.query_id, 64)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> NFTRevokeBody:
        """
        Deserialize revoke body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTRevokeBody instance
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
        Initialize NFT transfer message body.

        :param destination: New owner address
        :param response_address: Address for excess funds (default: None)
        :param custom_payload: Optional custom payload cell
        :param forward_payload: Optional payload to forward to new owner
        :param forward_amount: Amount to forward in nanotons (default: 1)
        :param query_id: Query identifier (default: 0)
        """
        self.query_id = query_id
        self.destination = destination
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_amount = forward_amount
        self.forward_payload = forward_payload

    def serialize(self) -> Cell:
        """
        Serialize transfer body to Cell.

        Layout: op_code:uint32 query_id:uint64 destination:address response:address
                custom_payload:^Cell forward_amount:coins forward_payload:^Cell

        :return: Serialized message body cell
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
        """
        Deserialize transfer body from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized NFTTransferBody instance
        """
        raise NotImplementedError
