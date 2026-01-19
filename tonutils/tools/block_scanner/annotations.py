import typing as t

from tonutils.tools.block_scanner.events import (
    BlockEvent,
    EventBase,
    TransactionEvent,
    TransactionsEvent,
)

TEvent = t.TypeVar("TEvent", bound=EventBase)

Handler = t.Callable[[TEvent], t.Awaitable[None]]
Where = t.Callable[[TEvent], t.Union[bool, t.Awaitable[bool]]]

BlockWhere = t.Callable[[BlockEvent], t.Union[bool, t.Awaitable[bool]]]
TransactionWhere = t.Callable[[TransactionEvent], t.Union[bool, t.Awaitable[bool]]]
TransactionsWhere = t.Callable[[TransactionsEvent], t.Union[bool, t.Awaitable[bool]]]

AnyHandler = t.Callable[[EventBase], t.Awaitable[None]]
AnyWhere = t.Callable[[EventBase], t.Union[bool, t.Awaitable[bool]]]

HandlerEntry = t.Tuple[AnyHandler, t.Optional[AnyWhere]]
Decorator = t.Callable[[Handler[TEvent]], Handler[TEvent]]
