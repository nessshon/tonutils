import typing as t
from dataclasses import dataclass, field

from ton_core import BlockIdExt, Transaction

from tonutils.clients import LiteBalancer, LiteClient


@dataclass(frozen=True, slots=True)
class _BaseEvent:
    """Base event for ``BlockScanner``."""

    client: LiteBalancer | LiteClient
    """Lite client or balancer."""

    mc_block: BlockIdExt
    """Masterchain block being processed."""

    context: t.Mapping[str, t.Any]
    """Shared user context."""


@dataclass(frozen=True, slots=True)
class ErrorEvent(_BaseEvent):
    """Error raised during scanning or handler execution."""

    error: BaseException
    """Raised exception."""

    event: t.Any = None
    """Related event, or ``None``."""

    handler: t.Any = None
    """Handler that raised, or ``None``."""

    block: BlockIdExt | None = None
    """Related shard block, or ``None``."""


@dataclass(frozen=True, slots=True)
class BlockEvent(_BaseEvent):
    """Shard block discovered by the scanner."""

    block: BlockIdExt
    """Shard block identifier."""


@dataclass(frozen=True, slots=True)
class TransactionsEvent(_BaseEvent):
    """Transactions fetched for a shard block."""

    block: BlockIdExt
    """Shard block identifier."""

    transactions: list[Transaction] = field(default_factory=list)
    """Transactions from this block."""
