import typing as t
from dataclasses import dataclass, field

from pytoniq_core import Transaction
from pytoniq_core.tl import BlockIdExt

from tonutils.clients import LiteBalancer, LiteClient


@dataclass(frozen=True, slots=True)
class EventBase:
    client: t.Union[LiteBalancer, LiteClient]
    mc_block: BlockIdExt
    context: t.Dict[str, t.Any]


@dataclass(frozen=True, slots=True)
class BlockEvent(EventBase):
    block: BlockIdExt


@dataclass(frozen=True, slots=True)
class TransactionEvent(EventBase):
    block: BlockIdExt
    transaction: Transaction


@dataclass(frozen=True, slots=True)
class TransactionsEvent(EventBase):
    block: BlockIdExt
    transactions: t.List[Transaction] = field(default_factory=list)
