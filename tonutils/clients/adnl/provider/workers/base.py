from __future__ import annotations

import asyncio
import typing as t
from abc import ABC, abstractmethod
from contextlib import suppress

if t.TYPE_CHECKING:
    from tonutils.clients.adnl.provider import AdnlProvider


class BaseWorker(ABC):
    """Base class for background workers used by ADNL providers."""

    def __init__(self, provider: AdnlProvider) -> None:
        """
        :param provider: Owning ADNL provider.
        """
        self.provider = provider

        self._running: bool = False
        self._task: t.Optional[asyncio.Task] = None

    @property
    def running(self) -> bool:
        """Whether the worker task is active and not finished."""
        return self._running and self._task is not None and not self._task.done()

    async def start(self) -> None:
        """Start the worker if not already running."""
        if self._task is not None and not self._task.done():
            return

        self._running = True
        self._task = asyncio.create_task(
            self._run_wrapper(),
            name=self.__class__.__name__,
        )

    async def stop(self) -> None:
        """Stop the worker and await its background task."""
        self._running = False
        task, self._task = self._task, None

        if task is None:
            return
        if task.done():
            with suppress(asyncio.CancelledError):
                await task
            return

        task.cancel()

        if task is asyncio.current_task():
            return
        with suppress(asyncio.CancelledError):
            await task

    async def _run_wrapper(self) -> None:
        """Run `_run` with lifecycle management and exception suppression."""
        try:
            await self._run()
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False

    @abstractmethod
    async def _run(self) -> None:
        """Worker loop executed while the worker is running."""
        raise NotImplementedError
