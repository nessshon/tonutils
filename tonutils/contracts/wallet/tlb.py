from __future__ import annotations

import abc
import typing as t

from pytoniq_core import (
    Builder,
    Cell,
    Slice,
    TlbScheme,
    begin_cell,
    WalletMessage,
    MessageAny,
)

from tonutils.contracts.opcodes import OpCode
from tonutils.types import (
    NetworkGlobalID,
    PublicKey,
    WorkchainID,
    DEFAULT_SUBWALLET_ID,
)


class BaseWalletData(TlbScheme, abc.ABC):
    """
    Abstract base class for wallet on-chain data structures.

    Defines the common interface for serializing and deserializing
    wallet state data stored on the blockchain.
    """

    def __init__(self, public_key: PublicKey) -> None:
        """
        Initialize base wallet data.

        :param public_key: Ed25519 public key instance for the wallet
        """
        self.public_key = public_key


class WalletV1Data(BaseWalletData):
    """On-chain data structure for Wallet v1 contracts."""

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
    ) -> None:
        """
        Initialize Wallet v1 data.

        :param public_key: Ed25519 public key instance
        :param seqno: Sequence number (default: 0)
        """
        super().__init__(public_key)
        self.seqno = seqno

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: seqno:uint32 public_key:bits256

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_uint(self.seqno, 32)
        cell.store_bytes(self.public_key.as_bytes)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV1Data:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized WalletV1Data instance
        """
        return cls(
            seqno=cs.load_uint(32),
            public_key=PublicKey(cs.load_bytes(32)),
        )


class WalletV2Data(WalletV1Data):
    """On-chain data structure for Wallet v2 contracts."""


class WalletV3Data(BaseWalletData):
    """On-chain data structure for Wallet v3 contracts."""

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
    ) -> None:
        """
        Initialize Wallet v3 data.

        :param public_key: Ed25519 public key instance
        :param seqno: Sequence number (default: 0)
        :param subwallet_id: Subwallet identifier (default: 698983191)
        """
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: seqno:uint32 subwallet_id:uint32 public_key:bits256

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_uint(self.seqno, 32)
        cell.store_uint(self.subwallet_id, 32)
        cell.store_bytes(self.public_key.as_bytes)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV3Data:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized WalletV3Data instance
        """
        return cls(
            seqno=cs.load_uint(32),
            subwallet_id=cs.load_uint(32),
            public_key=PublicKey(cs.load_bytes(32)),
        )


class WalletV4Data(BaseWalletData):
    """On-chain data structure for Wallet v4 contracts."""

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
        plugins: t.Optional[Cell] = None,
    ) -> None:
        """
        Initialize Wallet v4 data.

        :param public_key: Ed25519 public key instance
        :param seqno: Sequence number (default: 0)
        :param subwallet_id: Subwallet identifier (default: 698983191)
        :param plugins: Dictionary cell of installed plugins (default: None)
        """
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id
        self.plugins = plugins

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: seqno:uint32 subwallet_id:uint32 public_key:bits256 plugins:dict

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_uint(self.seqno, 32)
        cell.store_uint(self.subwallet_id, 32)
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_dict(self.plugins)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV4Data:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized WalletV4Data instance
        """
        return cls(
            seqno=cs.load_uint(32),
            subwallet_id=cs.load_uint(32),
            public_key=PublicKey(cs.load_bytes(32)),
            plugins=cs.load_maybe_ref(),
        )


class WalletV5SubwalletID:
    """
    Enhanced subwallet identifier for Wallet v5 contracts.

    Encodes network, workchain, version, and subwallet number into
    a single 32-bit value for improved wallet isolation.
    """

    def __init__(
        self,
        subwallet_number: int = 0,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        version: int = 0,
        network_global_id: NetworkGlobalID = NetworkGlobalID.MAINNET,
    ) -> None:
        """
        Initialize Wallet v5 subwallet ID.

        :param subwallet_number: Subwallet number (0-32767)
        :param workchain: Target workchain (default: BASECHAIN)
        :param version: Wallet version identifier (default: 0)
        :param network_global_id: Network identifier (default: MAINNET)
        """
        self.subwallet_number = subwallet_number
        self.workchain = workchain
        self.version = version
        self.network_global_id = network_global_id

    def pack(self) -> int:
        """
        Pack subwallet ID components into 32-bit integer.

        Format: (1 << 31) | (workchain << 23) | (version << 15) | subwallet_number
        XORed with network_global_id for network isolation.

        :return: Packed 32-bit subwallet ID
        """
        ctx = 0
        ctx |= 1 << 31
        ctx |= (self.workchain & 0xFF) << 23
        ctx |= (self.version & 0xFF) << 15
        ctx |= self.subwallet_number & 0x7FFF
        return ctx ^ (self.network_global_id & 0xFFFFFFFF)

    @classmethod
    def unpack(
        cls,
        value: int,
        network_global_id: NetworkGlobalID,
    ) -> WalletV5SubwalletID:
        """
        Unpack 32-bit integer into subwallet ID components.

        :param value: Packed 32-bit subwallet ID
        :param network_global_id: Network identifier for XOR decoding
        :return: Unpacked WalletV5SubwalletID instance
        """
        ctx = (value ^ network_global_id) & 0xFFFFFFFF

        subwallet_number = ctx & 0x7FFF
        version = (ctx >> 15) & 0xFF
        wc_u8 = (ctx >> 23) & 0xFF
        workchain = (wc_u8 ^ 0x80) - 0x80

        return cls(
            subwallet_number=subwallet_number,
            workchain=WorkchainID(workchain),
            version=version,
            network_global_id=network_global_id,
        )

    def __repr__(self) -> str:
        return f"WalletV5SubwalletID<{self.pack()!r}>"


class WalletV5BetaData(BaseWalletData):
    """
    On-chain data structure for Wallet v5 Beta contracts.

    Experimental v5 implementation with enhanced subwallet ID.
    """

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: WalletV5SubwalletID,
        seqno: int = 0,
        plugins: t.Optional[Cell] = None,
    ) -> None:
        """
        Initialize Wallet v5 Beta data.

        :param public_key: Ed25519 public key instance
        :param subwallet_id: Enhanced subwallet identifier
        :param seqno: Sequence number (default: 0)
        :param plugins: Dictionary cell of installed plugins (default: None)
        """
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id
        self.plugins = plugins

    def _store_wallet_id(self, builder: Builder) -> None:
        """
        Store wallet ID components to builder.

        :param builder: Cell builder to store to
        """
        builder.store_int(self.subwallet_id.network_global_id, 32)
        builder.store_int(self.subwallet_id.workchain, 8)
        builder.store_uint(self.subwallet_id.version, 8)
        builder.store_uint(self.subwallet_id.subwallet_number, 32)

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: seqno:uint33 network_id:int32 workchain:int8 version:uint8
                subwallet_number:uint32 public_key:bits256 plugins:dict

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_uint(self.seqno, 33)
        self._store_wallet_id(cell)
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_dict(self.plugins)
        return cell.end_cell()

    @classmethod
    def _load_wallet_id(cls, cs: Slice) -> WalletV5SubwalletID:
        """
        Load wallet ID components from slice.

        :param cs: Cell slice to load from
        :return: Loaded WalletV5SubwalletID
        """
        return WalletV5SubwalletID(
            network_global_id=NetworkGlobalID(cs.load_int(32)),
            workchain=WorkchainID(cs.load_int(8)),
            version=cs.load_uint(8),
            subwallet_number=cs.load_uint(32),
        )

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV5BetaData:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized WalletV5BetaData instance
        """
        return cls(
            seqno=cs.load_uint(33),
            subwallet_id=cls._load_wallet_id(cs),
            public_key=PublicKey(cs.load_bytes(32)),
            plugins=cs.load_maybe_ref(),
        )


class WalletV5Data(BaseWalletData):
    """
    On-chain data structure for Wallet v5 contracts.

    Wallet version with signature control and packed subwallet ID.
    """

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: WalletV5SubwalletID,
        seqno: int = 0,
        plugins: t.Optional[Cell] = None,
        is_signature_allowed: bool = True,
    ) -> None:
        """
        Initialize Wallet v5 data.

        :param public_key: Ed25519 public key instance
        :param subwallet_id: Enhanced subwallet identifier
        :param seqno: Sequence number (default: 0)
        :param plugins: Dictionary cell of installed plugins (default: None)
        :param is_signature_allowed: Whether signature auth is enabled (default: True)
        """
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id
        self.plugins = plugins
        self.is_signature_allowed = is_signature_allowed

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: is_signature_allowed:bool seqno:uint32 subwallet_id:uint32
                public_key:bits256 plugins:dict

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_bool(self.is_signature_allowed)
        cell.store_uint(self.seqno, 32)
        cell.store_uint(self.subwallet_id.pack(), 32)
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_dict(self.plugins)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice, network_global_id: NetworkGlobalID) -> WalletV5Data:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :param network_global_id: Network ID for unpacking subwallet_id
        :return: Deserialized WalletV5Data instance
        """
        return cls(
            is_signature_allowed=cs.load_bool(),
            seqno=cs.load_uint(32),
            subwallet_id=WalletV5SubwalletID.unpack(
                cs.load_uint(32), network_global_id
            ),
            public_key=PublicKey(cs.load_bytes(32)),
            plugins=cs.load_maybe_ref(),
        )


class WalletHighloadV2Data(BaseWalletData):
    """
    On-chain data structure for Highload Wallet v2 contracts.

    Optimized for high transaction throughput with query-based replay protection.
    """

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
        last_cleaned: int = 0,
        old_queries: t.Optional[Cell] = None,
    ) -> None:
        """
        Initialize Highload Wallet v2 data.

        :param public_key: Ed25519 public key instance
        :param subwallet_id: Subwallet identifier (default: 698983191)
        :param last_cleaned: Timestamp of last cleanup (default: 0)
        :param old_queries: Dictionary of processed query IDs (default: None)
        """
        super().__init__(public_key)
        self.subwallet_id = subwallet_id
        self.last_cleaned = last_cleaned
        self.old_queries = old_queries

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: subwallet_id:uint32 last_cleaned:uint64 public_key:bits256 old_queries:dict

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_uint(self.subwallet_id, 32)
        cell.store_uint(self.last_cleaned, 64)
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_dict(self.old_queries)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletHighloadV2Data:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized WalletHighloadV2Data instance
        """
        return cls(
            subwallet_id=cs.load_uint(32),
            last_cleaned=cs.load_uint(64),
            public_key=PublicKey(cs.load_bytes(32)),
            old_queries=cs.load_maybe_ref(),
        )


class WalletHighloadV3Data(BaseWalletData):
    """
    On-chain data structure for Highload Wallet v3 contracts.

    Improved highload wallet with separate old/new query tracking.
    """

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
        old_queries: t.Optional[Cell] = None,
        queries: t.Optional[Cell] = None,
        last_clean_time: int = 0,
        timeout: int = 60 * 5,
    ) -> None:
        """
        Initialize Highload Wallet v3 data.

        :param public_key: Ed25519 public key instance
        :param subwallet_id: Subwallet identifier (default: 698983191)
        :param old_queries: Dictionary of old processed query IDs (default: None)
        :param queries: Dictionary of current processed query IDs (default: None)
        :param last_clean_time: Timestamp of last cleanup (default: 0)
        :param timeout: Query expiration timeout in seconds (default: 300)
        """
        super().__init__(public_key)
        self.subwallet_id = subwallet_id
        self.old_queries = old_queries
        self.queries = queries
        self.last_clean_time = last_clean_time
        self.timeout = timeout

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: public_key:bits256 subwallet_id:uint32 old_queries:dict
                queries:dict last_clean_time:uint64 timeout:uint22

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_uint(self.subwallet_id, 32)
        cell.store_dict(self.old_queries)
        cell.store_dict(self.queries)
        cell.store_uint(self.last_clean_time, 64)
        cell.store_uint(self.timeout, 22)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletHighloadV3Data:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized WalletHighloadV3Data instance
        """
        return cls(
            public_key=PublicKey(cs.load_bytes(32)),
            subwallet_id=cs.load_uint(32),
            old_queries=cs.load_maybe_ref(),
            queries=cs.load_maybe_ref(),
            last_clean_time=cs.load_uint(64),
            timeout=cs.load_uint(22),
        )


class WalletPreprocessedV2Data(BaseWalletData):
    """
    On-chain data structure for Preprocessed Wallet v2 contracts.

    Special wallet for handling preprocessed external messages.
    """

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
    ) -> None:
        """
        Initialize Preprocessed Wallet v2 data.

        :param public_key: Ed25519 public key instance
        :param seqno: Sequence number (default: 0)
        """
        super().__init__(public_key)
        self.seqno = seqno

    def serialize(self) -> Cell:
        """
        Serialize wallet data to Cell.

        Layout: public_key:bits256 seqno:uint16

        :return: Serialized data cell
        """
        cell = begin_cell()
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_uint(self.seqno, 16)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletPreprocessedV2Data:
        """
        Deserialize wallet data from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized WalletPreprocessedV2Data instance
        """
        return cls(
            public_key=PublicKey(cs.load_bytes(32)),
            seqno=cs.load_uint(16),
        )


class OutActionSendMsg(TlbScheme):
    """
    Output action for sending messages from wallet contracts.

    Represents a single message in the wallet's action list with
    send mode and message data.
    """

    def __init__(self, message: WalletMessage) -> None:
        """
        Initialize output action.

        :param message: Wallet message containing send mode and internal message
        """
        self.message = message

    def serialize(self) -> Cell:
        """
        Serialize output action to Cell.

        Layout: op_code:uint32 send_mode:uint8 message:^Cell

        :return: Serialized action cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.OUT_ACTION_SEND_MSG, 32)
        cell.store_uint(self.message.send_mode, 8)
        cell.store_ref(self.message.message.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> OutActionSendMsg:
        """
        Deserialize output action from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized OutActionSendMsg instance
        """
        cs.skip_bits(32)
        send_mode = cs.load_uint(8)
        message_slice = cs.load_ref().begin_parse()
        message = MessageAny.deserialize(message_slice)
        return cls(message=WalletMessage(send_mode, message))


class TextCommentBody(TlbScheme):
    """
    Message body containing plain text comment.

    Standard format for text comments in TON transfers (opcode 0x00000000).
    """

    def __init__(self, text: str) -> None:
        """
        Initialize text comment body.

        :param text: Text comment string
        """
        self.text = text

    def serialize(self) -> Cell:
        """
        Serialize text comment to Cell.

        Layout: op_code:uint32 text:snake_string

        :return: Serialized comment cell
        """
        cell = begin_cell()
        cell.store_uint(OpCode.TEXT_COMMENT, 32)
        cell.store_snake_string(self.text)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TextCommentBody:
        """
        Deserialize text comment from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized TextCommentBody instance
        """
        cs.skip_bits(32)
        return cls(cs.load_snake_string())


class EncryptedTextCommentBody(TlbScheme):
    """
    Message body containing encrypted text comment.

    Standard format for encrypted comments in TON transfers (opcode 0x2167DA4B).
    Uses AES-CBC encryption with shared secret derived from ECDH.
    """

    def __init__(
        self,
        pub_xor: bytes,
        msg_key: bytes,
        ciphertext: bytes,
    ) -> None:
        """
        Initialize encrypted text comment body.

        :param pub_xor: XORed public key (32 bytes)
        :param msg_key: Message key for AES (16 bytes)
        :param ciphertext: Encrypted message bytes
        """
        self.pub_xor = pub_xor
        self.msg_key = msg_key
        self.ciphertext = ciphertext

    def serialize(self) -> Cell:
        """
        Serialize encrypted comment to Cell.

        Layout: op_code:uint32 payload:snake_bytes
        Payload: pub_xor(32) + msg_key(16) + ciphertext

        :return: Serialized encrypted comment cell
        """
        payload = self.pub_xor + self.msg_key + self.ciphertext
        cell = begin_cell()
        cell.store_uint(OpCode.ENCRYPTED_TEXT_COMMENT, 32)
        cell.store_snake_bytes(payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> EncryptedTextCommentBody:
        """
        Deserialize encrypted comment from Cell slice.

        :param cs: Cell slice to deserialize from
        :return: Deserialized EncryptedTextCommentBody instance
        """
        cs.skip_bits(32)
        payload = cs.load_snake_bytes()
        return cls(payload[:32], payload[32:48], payload[48:])
