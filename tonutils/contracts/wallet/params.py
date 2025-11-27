import secrets
import time
import typing as t
from dataclasses import dataclass

from tonutils.contracts.opcodes import OpCode
from tonutils.types import SendMode, DEFAULT_SENDMODE


@dataclass
class BaseWalletParams: ...


@dataclass
class WalletV1Params(BaseWalletParams):
    seqno: t.Optional[int] = None


@dataclass
class WalletV2Params(BaseWalletParams):
    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None


@dataclass
class WalletV3Params(BaseWalletParams):
    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None


@dataclass
class WalletV4Params(BaseWalletParams):
    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None
    op_code: int = 0x00


@dataclass
class WalletV5BetaParams(BaseWalletParams):
    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None
    op_code: int = OpCode.AUTH_SIGNED_EXTERNAL


@dataclass
class WalletV5Params(BaseWalletParams):
    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None
    op_code: int = OpCode.AUTH_SIGNED_EXTERNAL


@dataclass
class WalletHighloadV2Params(BaseWalletParams):
    bounded_id: t.Optional[int] = None
    query_id: t.Optional[int] = None
    message_ttl: int = 60 * 5

    def __post_init__(self) -> None:
        if self.query_id is None:
            self.query_id = secrets.randbits(32)
        if self.bounded_id is None:
            now = int(time.time())
            ttl_u32 = (now + self.message_ttl) & 0xFFFFFFFF
            qid_u32 = self.query_id & 0xFFFFFFFF
            self.bounded_id = (ttl_u32 << 32) | qid_u32


@dataclass
class WalletHighloadV3Params(BaseWalletParams):
    value_to_send: t.Optional[int] = None
    created_at: t.Optional[int] = None
    query_id: t.Optional[int] = None
    send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = int(time.time() - 60)
        if self.query_id is None:
            self.query_id = (self.created_at % (1 << 23)) & 0xFFFFFFFF


@dataclass
class WalletPreprocessedV2Params(BaseWalletParams):
    seqno: t.Optional[int] = None
    valid_until: t.Optional[int] = None
