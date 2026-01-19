import asyncio
import inspect
import traceback
import typing as t

from tonutils.tools.block_scanner.annotations import (
    AnyHandler,
    AnyWhere,
    Decorator,
    Handler,
    HandlerEntry,
    TEvent,
    Where,
)
from tonutils.tools.block_scanner.events import EventBase


class EventDispatcher:
    """Dispatches events to registered handlers asynchronously."""

    def __init__(self, max_concurrency: int = 1000) -> None:
        """
        Initialize EventDispatcher.

        :param max_concurrency: maximum number of concurrent handler tasks.
        """
        self._handlers: t.Dict[t.Type[EventBase], t.List[HandlerEntry]] = {}
        self._sem = asyncio.Semaphore(max(1, max_concurrency))
        self._tasks: t.Set[asyncio.Task[None]] = set()
        self._closed = False

    def register(
        self,
        event_type: t.Type[TEvent],
        handler: Handler[TEvent],
        *,
        where: t.Optional[Where[TEvent]] = None,
    ) -> None:
        """
        Register a handler for a specific event type.

        :param event_type: subclass of EventBase to handle.
        :param handler: callable receiving the event.
        :param where: optional filter predicate. Handler is invoked only if predicate returns True.
        """
        if not callable(handler):
            raise TypeError("handler must be callable")

        entry: HandlerEntry = (
            t.cast(AnyHandler, handler),
            t.cast(t.Optional[AnyWhere], where),
        )
        self._handlers.setdefault(event_type, []).append(entry)

    def on(
        self,
        event_type: t.Type[TEvent],
        *,
        where: t.Optional[Where[TEvent]] = None,
    ) -> Decorator[TEvent]:
        """
        Decorator to register a handler for an event type.

        :param event_type: event class to handle.
        :param where: optional filter predicate.
        :return: Decorator that registers the handler.
        """

        def decorator(fn: Handler[TEvent]) -> Handler[TEvent]:
            self.register(event_type=event_type, handler=fn, where=where)
            return fn

        return decorator

    def _iter_handlers(self, event: EventBase) -> t.Sequence[HandlerEntry]:
        """Return all handlers matching the type of `event`."""
        out: t.List[HandlerEntry] = []
        for tp in type(event).mro():
            if tp is EventBase:
                break
            entries = self._handlers.get(t.cast(t.Type[EventBase], tp))
            if entries:
                out.extend(entries)
        return out

    def _on_task_done(self, task: asyncio.Task[None]) -> None:
        """Callback to handle task completion and print exceptions."""
        self._tasks.discard(task)
        try:
            exc = task.exception()
        except asyncio.CancelledError:
            return
        if exc is not None:
            traceback.print_exception(type(exc), exc, exc.__traceback__)

    async def _run_task(
        self,
        handler: AnyHandler,
        event: EventBase,
        where: t.Optional[AnyWhere] = None,
    ) -> None:
        """
        Run a single handler task with optional 'where' filtering.

        :param handler: async callable to execute.
        :param event: event instance to pass.
        :param where: optional predicate, skip handler if False.
        """
        async with self._sem:
            if where is not None:
                result = where(event)
                if inspect.isawaitable(result):
                    result = await result
                if not result:
                    return
            await handler(event)

    def emit(self, event: EventBase) -> None:
        """
        Emit an event to all matching handlers.

        Handlers are executed asynchronously.
        """
        if self._closed:
            return

        for handler, where in self._iter_handlers(event):
            task = asyncio.create_task(self._run_task(handler, event, where))
            self._tasks.add(task)
            task.add_done_callback(self._on_task_done)

    async def aclose(self) -> None:
        """
        Close the dispatcher and wait for all running handler tasks.

        After calling, no new events will be dispatched.
        """
        self._closed = True
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
