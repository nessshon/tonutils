import secrets
import time
import typing as t
from dataclasses import dataclass

from tonutils.contracts.opcodes import OpCode
from tonutils.types import SendMode, DEFAULT_SENDMODE


@dataclass
class BaseWalletParams:
    """Base parameters class for wallet transaction building."""


@dataclass
class WalletV1Params(BaseWalletParams):
    """Transaction parameters for Wallet v1 contracts."""

    seqno: t.Optional[int] = None
    """Sequence number for this transaction (fetched from contract if None)."""


@dataclass
class WalletV2Params(BaseWalletParams):
    """Transaction parameters for Wallet v2 contracts."""

    seqno: t.Optional[int] = None
    """Sequence number for this transaction (fetched from contract if None)."""

    valid_until: t.Optional[int] = None
    """Unix timestamp when transaction expires."""


@dataclass
class WalletV3Params(BaseWalletParams):
    """Transaction parameters for Wallet v3 contracts."""

    seqno: t.Optional[int] = None
    """Sequence number for this transaction (fetched from contract if None)."""

    valid_until: t.Optional[int] = None
    """Unix timestamp when transaction expires."""


@dataclass
class WalletV4Params(BaseWalletParams):
    """Transaction parameters for Wallet v4 contracts."""

    seqno: t.Optional[int] = None
    """Sequence number for this transaction (fetched from contract if None)."""

    valid_until: t.Optional[int] = None
    """Unix timestamp when transaction expires ."""

    op_code: int = 0x00
    """Operation code for the transaction (default: 0x00 for simple transfer)."""


@dataclass
class WalletV5BetaParams(BaseWalletParams):
    """Transaction parameters for Wallet v5 Beta contracts."""

    seqno: t.Optional[int] = None
    """Sequence number for this transaction (fetched from contract if None)."""

    valid_until: t.Optional[int] = None
    """Unix timestamp when transaction expires."""

    op_code: int = OpCode.AUTH_SIGNED_EXTERNAL
    """Operation code for the transaction (default: 0x7369676E)."""


@dataclass
class WalletV5Params(BaseWalletParams):
    """Transaction parameters for Wallet v5 contracts."""

    seqno: t.Optional[int] = None
    """Sequence number for this transaction (fetched from contract if None)."""

    valid_until: t.Optional[int] = None
    """Unix timestamp when transaction expires."""

    op_code: int = OpCode.AUTH_SIGNED_EXTERNAL
    """Operation code for the transaction (default: 0x7369676E)."""


@dataclass
class WalletHighloadV2Params(BaseWalletParams):
    """Transaction parameters for Highload Wallet v2 contracts."""

    bounded_id: t.Optional[int] = None
    """Bounded query ID combining TTL and query_id (auto-generated if None)."""

    query_id: t.Optional[int] = None
    """Random 32-bit query identifier (auto-generated if None)."""

    message_ttl: int = 60 * 5
    """Message time-to-live in seconds (default: 300 seconds)."""

    def __post_init__(self) -> None:
        """Auto-generate query_id and bounded_id if not provided."""
        if self.query_id is None:
            self.query_id = secrets.randbits(32)
        if self.bounded_id is None:
            now = int(time.time())
            ttl_u32 = (now + self.message_ttl) & 0xFFFFFFFF
            qid_u32 = self.query_id & 0xFFFFFFFF
            self.bounded_id = (ttl_u32 << 32) | qid_u32


@dataclass
class WalletHighloadV3Params(BaseWalletParams):
    """Transaction parameters for Highload Wallet v3 contracts."""

    value_to_send: t.Optional[int] = None
    """Total value to send in nanotons (calculated from messages if None)."""

    created_at: t.Optional[int] = None
    """Unix timestamp when transaction was created (auto-generated if None)."""

    query_id: t.Optional[int] = None
    """Query identifier derived from created_at (auto-generated if None)."""

    send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE
    """Message send mode (default: pay fees separately)."""

    def __post_init__(self) -> None:
        """Auto-generate created_at and query_id if not provided."""
        if self.created_at is None:
            self.created_at = int(time.time() - 60)
        if self.query_id is None:
            self.query_id = (self.created_at % (1 << 23)) & 0xFFFFFFFF


@dataclass
class WalletPreprocessedV2Params(BaseWalletParams):
    """Transaction parameters for Preprocessed Wallet v2 contracts."""

    seqno: t.Optional[int] = None
    """Sequence number for this transaction (fetched from contract if None)."""

    valid_until: t.Optional[int] = None
    """Unix timestamp when transaction expires."""
