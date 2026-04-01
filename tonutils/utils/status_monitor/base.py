from __future__ import annotations

import abc
import asyncio
import dataclasses
import time
import typing as t
from contextlib import suppress

if t.TYPE_CHECKING:
    from tonutils.utils.status_monitor.console import Console

_C = t.TypeVar("_C")
_S = t.TypeVar("_S")


class BaseMonitor(abc.ABC, t.Generic[_C, _S]):
    """Abstract base for real-time node health monitors with terminal UI."""

    RENDER_INTERVAL = 0.1
    """Seconds between terminal UI renders."""

    RECONNECT_INTERVAL = 30.0
    """Seconds to wait before reconnecting a failed client."""

    FAST_UPDATE_INTERVAL: t.ClassVar[float]
    """Seconds between fast update cycles (ping, seqno)."""

    MEDIUM_UPDATE_INTERVAL: t.ClassVar[float]
    """Seconds between medium update cycles (version, config)."""

    SLOW_UPDATE_INTERVAL: t.ClassVar[float]
    """Seconds between slow update cycles (archive depth)."""

    def __init__(
        self,
        clients: list[_C],
        console: Console,
    ) -> None:
        """Initialize the base monitor.

        :param clients: Node clients to monitor.
        :param console: Console renderer instance.
        """
        self._clients = clients
        self._console = console

        self._statuses: dict[int, _S] = {}
        self._last_connect: dict[int, float] = {}

        self._tasks: list[asyncio.Task[None]] = []
        self._stop = asyncio.Event()

        self._locks: dict[int, asyncio.Lock] = {}

    @property
    def statuses(self) -> list[_S]:
        """Current snapshot of all node statuses."""
        return list(self._statuses.values())

    async def run(self) -> None:
        """Start the monitor render loop (blocks until stopped)."""
        self._console.enter()
        self._init_statuses()
        self._start_update_loops()

        try:
            while not self._stop.is_set():
                self._console.render(self.statuses)
                await self._sleep(self.RENDER_INTERVAL)
        finally:
            self._console.exit()

    async def stop(self) -> None:
        """Stop all update tasks and close clients."""
        if self._stop.is_set():
            return
        self._stop.set()

        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

        close_tasks = [self._close_client(c) for c in self._clients]
        await asyncio.gather(*close_tasks, return_exceptions=True)

    async def _sleep(self, seconds: float) -> None:
        """Sleep interruptibly via the stop event."""
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(self._stop.wait(), timeout=seconds)

    async def _set_status(self, index: int, **kwargs: t.Any) -> None:
        """Update status fields atomically under a per-index lock."""
        async with self._locks[index]:
            current = self._statuses[index]
            self._statuses[index] = dataclasses.replace(current, **kwargs)  # type: ignore[type-var]

    async def _ensure_connected(self, index: int) -> bool:
        """Ensure client is connected, reconnecting if needed.

        :param index: Client index.
        :return: Whether the client is connected.
        """
        if self._is_connected(index):
            return True

        now = time.monotonic()
        last_attempt = self._last_connect.get(index, 0.0)
        if now - last_attempt < self.RECONNECT_INTERVAL:
            return False

        self._last_connect[index] = now
        await self._connect(index)
        return self._is_connected(index)

    def _start_update_loops(self) -> None:
        """Spawn fast, medium, and slow update tasks per client."""
        if self._tasks:
            return

        for index in range(len(self._clients)):
            self._tasks.append(asyncio.create_task(self._fast_update_loop(index)))
            self._tasks.append(asyncio.create_task(self._medium_update_loop(index)))
            self._tasks.append(asyncio.create_task(self._slow_update_loop(index)))

    @abc.abstractmethod
    def _init_statuses(self) -> None:
        """Initialize status entries for all clients."""

    @abc.abstractmethod
    def _is_connected(self, index: int) -> bool:
        """Check whether client at *index* is connected.

        :param index: Client index.
        :return: ``True`` if connected.
        """

    @abc.abstractmethod
    async def _connect(self, index: int) -> None:
        """Connect (or reconnect) the client at *index*.

        :param index: Client index.
        """

    @abc.abstractmethod
    async def _close_client(self, client: _C) -> None:
        """Close a single client.

        :param client: Client instance.
        """

    @abc.abstractmethod
    async def _fast_update_loop(self, index: int) -> None:
        """Fast-interval update loop for client at *index*."""

    @abc.abstractmethod
    async def _medium_update_loop(self, index: int) -> None:
        """Medium-interval update loop for client at *index*."""

    @abc.abstractmethod
    async def _slow_update_loop(self, index: int) -> None:
        """Slow-interval update loop for client at *index*."""
