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
    """Abstract base for wallet on-chain data structures."""

    def __init__(self, public_key: PublicKey) -> None:
        """
        :param public_key: Ed25519 public key.
        """
        self.public_key = public_key


class WalletV1Data(BaseWalletData):
    """On-chain data for Wallet v1."""

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
    ) -> None:
        """
        :param public_key: Ed25519 public key.
        :param seqno: Sequence number.
        """
        super().__init__(public_key)
        self.seqno = seqno

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `seqno:uint32 public_key:bits256`
        """
        cell = begin_cell()
        cell.store_uint(self.seqno, 32)
        cell.store_bytes(self.public_key.as_bytes)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV1Data:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            seqno=cs.load_uint(32),
            public_key=PublicKey(cs.load_bytes(32)),
        )


class WalletV2Data(WalletV1Data):
    """On-chain data for Wallet v2."""


class WalletV3Data(BaseWalletData):
    """On-chain data for Wallet v3."""

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
    ) -> None:
        """
        :param public_key: Ed25519 public key.
        :param seqno: Sequence number.
        :param subwallet_id: Subwallet identifier.
        """
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `seqno:uint32 subwallet_id:uint32 public_key:bits256`
        """
        cell = begin_cell()
        cell.store_uint(self.seqno, 32)
        cell.store_uint(self.subwallet_id, 32)
        cell.store_bytes(self.public_key.as_bytes)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV3Data:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            seqno=cs.load_uint(32),
            subwallet_id=cs.load_uint(32),
            public_key=PublicKey(cs.load_bytes(32)),
        )


class WalletV4Data(BaseWalletData):
    """On-chain data for Wallet v4."""

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
        plugins: t.Optional[Cell] = None,
    ) -> None:
        """
        :param public_key: Ed25519 public key.
        :param seqno: Sequence number.
        :param subwallet_id: Subwallet identifier.
        :param plugins: Plugins dictionary cell, or `None`.
        """
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id
        self.plugins = plugins

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `seqno:uint32 subwallet_id:uint32 public_key:bits256 plugins:dict`
        """
        cell = begin_cell()
        cell.store_uint(self.seqno, 32)
        cell.store_uint(self.subwallet_id, 32)
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_dict(self.plugins)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV4Data:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            seqno=cs.load_uint(32),
            subwallet_id=cs.load_uint(32),
            public_key=PublicKey(cs.load_bytes(32)),
            plugins=cs.load_maybe_ref(),
        )


class WalletV5SubwalletID:
    """Enhanced subwallet identifier for Wallet v5.

    Packs network, workchain, version, and subwallet number
    into a single 32-bit value.
    """

    def __init__(
        self,
        subwallet_number: int = 0,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        version: int = 0,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
    ) -> None:
        """
        :param subwallet_number: Subwallet number (0–32767).
        :param workchain: Target workchain.
        :param version: Wallet version identifier.
        :param network: Network identifier.
        """
        self.subwallet_number = subwallet_number
        self.workchain = workchain
        self.version = version
        self.network = network

    def pack(self) -> int:
        """Pack components into a 32-bit integer.

        Format: `(1 << 31) | (workchain << 23) | (version << 15) | subwallet_number`
        XORed with the network global ID.
        """
        ctx = 0
        ctx |= 1 << 31
        ctx |= (self.workchain & 0xFF) << 23
        ctx |= (self.version & 0xFF) << 15
        ctx |= self.subwallet_number & 0x7FFF
        return ctx ^ (self.network & 0xFFFFFFFF)

    @classmethod
    def unpack(
        cls,
        value: int,
        network: NetworkGlobalID,
    ) -> WalletV5SubwalletID:
        """Unpack a 32-bit integer into components.

        :param value: Packed 32-bit subwallet ID.
        :param network: Network identifier for XOR decoding.
        """
        ctx = (value ^ network) & 0xFFFFFFFF

        subwallet_number = ctx & 0x7FFF
        version = (ctx >> 15) & 0xFF
        wc_u8 = (ctx >> 23) & 0xFF
        workchain = (wc_u8 ^ 0x80) - 0x80

        return cls(
            subwallet_number=subwallet_number,
            workchain=WorkchainID(workchain),
            version=version,
            network=network,
        )

    def __repr__(self) -> str:
        return f"WalletV5SubwalletID<{self.pack()!r}>"


class WalletV5BetaData(BaseWalletData):
    """On-chain data for Wallet v5 Beta."""

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: WalletV5SubwalletID,
        seqno: int = 0,
        plugins: t.Optional[Cell] = None,
    ) -> None:
        """
        :param public_key: Ed25519 public key.
        :param subwallet_id: Enhanced subwallet identifier.
        :param seqno: Sequence number.
        :param plugins: Plugins dictionary cell, or `None`.
        """
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id
        self.plugins = plugins

    def _store_wallet_id(self, builder: Builder) -> None:
        """Store wallet ID components into a `Builder`.

        :param builder: Target builder.
        """
        builder.store_int(self.subwallet_id.network, 32)
        builder.store_int(self.subwallet_id.workchain, 8)
        builder.store_uint(self.subwallet_id.version, 8)
        builder.store_uint(self.subwallet_id.subwallet_number, 32)

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `seqno:uint33 network_id:int32 workchain:int8 version:uint8
        subwallet_number:uint32 public_key:bits256 plugins:dict`
        """
        cell = begin_cell()
        cell.store_uint(self.seqno, 33)
        self._store_wallet_id(cell)
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_dict(self.plugins)
        return cell.end_cell()

    @classmethod
    def _load_wallet_id(cls, cs: Slice) -> WalletV5SubwalletID:
        """Load wallet ID components from a `Slice`.

        :param cs: Source slice.
        """
        return WalletV5SubwalletID(
            network=NetworkGlobalID(cs.load_int(32)),
            workchain=WorkchainID(cs.load_int(8)),
            version=cs.load_uint(8),
            subwallet_number=cs.load_uint(32),
        )

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletV5BetaData:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            seqno=cs.load_uint(33),
            subwallet_id=cls._load_wallet_id(cs),
            public_key=PublicKey(cs.load_bytes(32)),
            plugins=cs.load_maybe_ref(),
        )


class WalletV5Data(BaseWalletData):
    """On-chain data for Wallet v5."""

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: WalletV5SubwalletID,
        seqno: int = 0,
        plugins: t.Optional[Cell] = None,
        is_signature_allowed: bool = True,
    ) -> None:
        """
        :param public_key: Ed25519 public key.
        :param subwallet_id: Enhanced subwallet identifier.
        :param seqno: Sequence number.
        :param plugins: Plugins dictionary cell, or `None`.
        :param is_signature_allowed: Whether signature auth is enabled.
        """
        super().__init__(public_key)
        self.seqno = seqno
        self.subwallet_id = subwallet_id
        self.plugins = plugins
        self.is_signature_allowed = is_signature_allowed

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `is_signature_allowed:bool seqno:uint32 subwallet_id:uint32
        public_key:bits256 plugins:dict`
        """
        cell = begin_cell()
        cell.store_bool(self.is_signature_allowed)
        cell.store_uint(self.seqno, 32)
        cell.store_uint(self.subwallet_id.pack(), 32)
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_dict(self.plugins)
        return cell.end_cell()

    @classmethod
    def deserialize(
        cls,
        cs: Slice,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
    ) -> WalletV5Data:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        :param network: Network ID for unpacking subwallet_id.
        """
        return cls(
            is_signature_allowed=cs.load_bool(),
            seqno=cs.load_uint(32),
            subwallet_id=WalletV5SubwalletID.unpack(cs.load_uint(32), network),
            public_key=PublicKey(cs.load_bytes(32)),
            plugins=cs.load_maybe_ref(),
        )


class WalletHighloadV2Data(BaseWalletData):
    """On-chain data for Highload Wallet v2."""

    def __init__(
        self,
        public_key: PublicKey,
        subwallet_id: int = DEFAULT_SUBWALLET_ID,
        last_cleaned: int = 0,
        old_queries: t.Optional[Cell] = None,
    ) -> None:
        """
        :param public_key: Ed25519 public key.
        :param subwallet_id: Subwallet identifier.
        :param last_cleaned: Timestamp of last query cleanup.
        :param old_queries: Processed query IDs dictionary, or `None`.
        """
        super().__init__(public_key)
        self.subwallet_id = subwallet_id
        self.last_cleaned = last_cleaned
        self.old_queries = old_queries

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `subwallet_id:uint32 last_cleaned:uint64 public_key:bits256
        old_queries:dict`
        """
        cell = begin_cell()
        cell.store_uint(self.subwallet_id, 32)
        cell.store_uint(self.last_cleaned, 64)
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_dict(self.old_queries)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletHighloadV2Data:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            subwallet_id=cs.load_uint(32),
            last_cleaned=cs.load_uint(64),
            public_key=PublicKey(cs.load_bytes(32)),
            old_queries=cs.load_maybe_ref(),
        )


class WalletHighloadV3Data(BaseWalletData):
    """On-chain data for Highload Wallet v3."""

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
        :param public_key: Ed25519 public key.
        :param subwallet_id: Subwallet identifier.
        :param old_queries: Old processed query IDs, or `None`.
        :param queries: Current processed query IDs, or `None`.
        :param last_clean_time: Timestamp of last cleanup.
        :param timeout: Query expiration timeout in seconds.
        """
        super().__init__(public_key)
        self.subwallet_id = subwallet_id
        self.old_queries = old_queries
        self.queries = queries
        self.last_clean_time = last_clean_time
        self.timeout = timeout

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `public_key:bits256 subwallet_id:uint32 old_queries:dict
        queries:dict last_clean_time:uint64 timeout:uint22`
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
        """Deserialize from `Slice`.

        :param cs: Source slice.
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
    """On-chain data for Preprocessed Wallet v2."""

    def __init__(
        self,
        public_key: PublicKey,
        seqno: int = 0,
    ) -> None:
        """
        :param public_key: Ed25519 public key.
        :param seqno: Sequence number.
        """
        super().__init__(public_key)
        self.seqno = seqno

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `public_key:bits256 seqno:uint16`
        """
        cell = begin_cell()
        cell.store_bytes(self.public_key.as_bytes)
        cell.store_uint(self.seqno, 16)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> WalletPreprocessedV2Data:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        return cls(
            public_key=PublicKey(cs.load_bytes(32)),
            seqno=cs.load_uint(16),
        )


class OutActionSendMsg(TlbScheme):
    """Output action for sending a message from a wallet contract."""

    def __init__(self, message: WalletMessage) -> None:
        """
        :param message: Wallet message with send mode and internal message.
        """
        self.message = message

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 send_mode:uint8 message:^Cell`
        """
        cell = begin_cell()
        cell.store_uint(OpCode.OUT_ACTION_SEND_MSG, 32)
        cell.store_uint(self.message.send_mode, 8)
        cell.store_ref(self.message.message.serialize())
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> OutActionSendMsg:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        cs.skip_bits(32)
        send_mode = cs.load_uint(8)
        message_slice = cs.load_ref().begin_parse()
        message = MessageAny.deserialize(message_slice)
        return cls(message=WalletMessage(send_mode, message))


class TextCommentBody(TlbScheme):
    """Plain text comment body (opcode 0x00000000)."""

    def __init__(self, text: str) -> None:
        """
        :param text: Comment text.
        """
        self.text = text

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 text:snake_string`
        """
        cell = begin_cell()
        cell.store_uint(OpCode.TEXT_COMMENT, 32)
        cell.store_snake_string(self.text)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> TextCommentBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        cs.skip_bits(32)
        return cls(cs.load_snake_string())


class EncryptedTextCommentBody(TlbScheme):
    """Encrypted text comment body (opcode 0x2167DA4B)."""

    def __init__(
        self,
        pub_xor: bytes,
        msg_key: bytes,
        ciphertext: bytes,
    ) -> None:
        """
        :param pub_xor: XORed public key (32 bytes).
        :param msg_key: AES message key (16 bytes).
        :param ciphertext: Encrypted message bytes.
        """
        self.pub_xor = pub_xor
        self.msg_key = msg_key
        self.ciphertext = ciphertext

    def serialize(self) -> Cell:
        """Serialize to `Cell`.

        TLB: `op_code:uint32 payload:snake_bytes`

        Payload: `pub_xor(32) + msg_key(16) + ciphertext`
        """
        payload = self.pub_xor + self.msg_key + self.ciphertext
        cell = begin_cell()
        cell.store_uint(OpCode.ENCRYPTED_TEXT_COMMENT, 32)
        cell.store_snake_bytes(payload)
        return cell.end_cell()

    @classmethod
    def deserialize(cls, cs: Slice) -> EncryptedTextCommentBody:
        """Deserialize from `Slice`.

        :param cs: Source slice.
        """
        cs.skip_bits(32)
        payload = cs.load_snake_bytes()
        return cls(payload[:32], payload[32:48], payload[48:])
