import typing as t
from dataclasses import dataclass, field

from pytoniq_core import Transaction
from pytoniq_core.tl import BlockIdExt

from tonutils.clients import LiteBalancer, LiteClient


@dataclass(frozen=True, slots=True)
class _BaseEvent:
    """Base event for BlockScanner.

    Attributes:
        client: Lite client/balancer.
        mc_block: Masterchain block being processed.
        context: Shared user context.
    """

    client: t.Union[LiteBalancer, LiteClient]
    mc_block: BlockIdExt
    context: t.Mapping[str, t.Any]


@dataclass(frozen=True, slots=True)
class ErrorEvent(_BaseEvent):
    """Error raised during scanning or handler execution.

    Attributes:
        client: Lite client/balancer.
        mc_block: Masterchain block being processed.
        context: Shared user context.
        error: Raised exception.
        event: Related event (if any).
        handler: Handler/callable that raised (if any).
        block: Related shard block (if any).
    """

    error: BaseException
    event: t.Any = None
    handler: t.Any = None
    block: t.Optional[BlockIdExt] = None


@dataclass(frozen=True, slots=True)
class BlockEvent(_BaseEvent):
    """Shard block event.

    Attributes:
        client: Lite client/balancer.
        mc_block: Masterchain block being processed.
        context: Shared user context.
        block: Shard block identifier.
    """

    block: BlockIdExt


@dataclass(frozen=True, slots=True)
class TransactionsEvent(_BaseEvent):
    """Transactions event for a shard block.

    Attributes:
        client: Lite client/balancer.
        mc_block: Masterchain block being processed.
        context: Shared user context.
        block: Shard block identifier.
        transactions: Transactions from this block.
    """

    block: BlockIdExt
    transactions: t.List[Transaction] = field(default_factory=list)
