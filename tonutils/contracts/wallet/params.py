import secrets
import time
import typing as t
from dataclasses import dataclass

from tonutils.contracts.opcodes import OpCode
from tonutils.types import SendMode, DEFAULT_SENDMODE


@dataclass
class BaseWalletParams:
    """Base parameters for wallet transaction building."""


@dataclass
class WalletV1Params(BaseWalletParams):
    """Transaction parameters for Wallet v1.

    Attributes:
        seqno: Sequence number (fetched from contract if `None`).
    """

    seqno: t.Optional[int] = None


@dataclass
class WalletV2Params(BaseWalletParams):
    """Transaction parameters for Wallet v2.

    Attributes:
        seqno: Sequence number (fetched from contract if `None`).
        valid_until: Expiration unix timestamp, or `None`.
    """

    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None


@dataclass
class WalletV3Params(BaseWalletParams):
    """Transaction parameters for Wallet v3.

    Attributes:
        seqno: Sequence number (fetched from contract if `None`).
        valid_until: Expiration unix timestamp, or `None`.
    """

    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None


@dataclass
class WalletV4Params(BaseWalletParams):
    """Transaction parameters for Wallet v4.

    Attributes:
        seqno: Sequence number (fetched from contract if `None`).
        valid_until: Expiration unix timestamp, or `None`.
        op_code: Operation code (0x00 for simple transfer).
    """

    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None
    op_code: int = 0x00


@dataclass
class WalletV5BetaParams(BaseWalletParams):
    """Transaction parameters for Wallet v5 Beta.

    Attributes:
        seqno: Sequence number (fetched from contract if `None`).
        valid_until: Expiration unix timestamp, or `None`.
        op_code: Operation code (default: 0x7369676E).
    """

    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None
    op_code: int = OpCode.AUTH_SIGNED_EXTERNAL


@dataclass
class WalletV5Params(BaseWalletParams):
    """Transaction parameters for Wallet v5.

    Attributes:
        seqno: Sequence number (fetched from contract if `None`).
        valid_until: Expiration unix timestamp, or `None`.
        op_code: Operation code (default: 0x7369676E).
    """

    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None
    op_code: int = OpCode.AUTH_SIGNED_EXTERNAL


@dataclass
class WalletHighloadV2Params(BaseWalletParams):
    """Transaction parameters for Highload Wallet v2.

    Attributes:
        bounded_id: Bounded query ID combining TTL and query_id (auto-generated if `None`).
        query_id: Random 32-bit query identifier (auto-generated if `None`).
        message_ttl: Message time-to-live in seconds (default: 300).
    """

    bounded_id: t.Optional[int] = None
    query_id: t.Optional[int] = None
    message_ttl: int = 60 * 5

    def __post_init__(self) -> None:
        """Auto-generate `query_id` and `bounded_id` if not provided."""
        if self.query_id is None:
            self.query_id = secrets.randbits(32)
        if self.bounded_id is None:
            now = int(time.time())
            ttl_u32 = (now + self.message_ttl) & 0xFFFFFFFF
            qid_u32 = self.query_id & 0xFFFFFFFF
            self.bounded_id = (ttl_u32 << 32) | qid_u32


@dataclass
class WalletHighloadV3Params(BaseWalletParams):
    """Transaction parameters for Highload Wallet v3.

    Attributes:
        value_to_send: Total value in nanotons (calculated from messages if `None`).
        created_at: Creation unix timestamp (auto-generated if `None`).
        query_id: Query identifier derived from `created_at` (auto-generated if `None`).
        send_mode: Message send mode flags.
    """

    value_to_send: t.Optional[int] = None
    created_at: t.Optional[int] = None
    query_id: t.Optional[int] = None
    send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE

    def __post_init__(self) -> None:
        """Auto-generate `created_at` and `query_id` if not provided."""
        if self.created_at is None:
            self.created_at = int(time.time() - 60)
        if self.query_id is None:
            self.query_id = (self.created_at % (1 << 23)) & 0xFFFFFFFF


@dataclass
class WalletPreprocessedV2Params(BaseWalletParams):
    """Transaction parameters for Preprocessed Wallet v2.

    Attributes:
        seqno: Sequence number (fetched from contract if `None`).
        valid_until: Expiration unix timestamp, or `None`.
    """

    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None
