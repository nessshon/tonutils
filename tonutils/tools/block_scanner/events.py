import typing as t
from dataclasses import dataclass, field

from pytoniq_core import Transaction
from pytoniq_core.tl import BlockIdExt

from tonutils.clients import LiteBalancer, LiteClient


@dataclass(frozen=True, slots=True)
class _BaseEvent:
    """Base event for `BlockScanner`.

    Attributes:
        client: Lite client or balancer.
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
        error: Raised exception.
        event: Related event, or `None`.
        handler: Handler that raised, or `None`.
        block: Related shard block, or `None`.
    """

    error: BaseException
    event: t.Any = None
    handler: t.Any = None
    block: t.Optional[BlockIdExt] = None


@dataclass(frozen=True, slots=True)
class BlockEvent(_BaseEvent):
    """Shard block discovered by the scanner.

    Attributes:
        block: Shard block identifier.
    """

    block: BlockIdExt


@dataclass(frozen=True, slots=True)
class TransactionsEvent(_BaseEvent):
    """Transactions fetched for a shard block.

    Attributes:
        block: Shard block identifier.
        transactions: Transactions from this block.
    """

    block: BlockIdExt
    transactions: t.List[Transaction] = field(default_factory=list)
