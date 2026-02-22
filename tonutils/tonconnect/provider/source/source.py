import asyncio
import typing as t
from contextlib import suppress

import aiohttp
from yarl import URL

from tonutils.tonconnect.provider.source.decoder import EventDecoder
from tonutils.tonconnect.provider.source.message import EventMessage
from tonutils.tonconnect.provider.source.state import ReadyState


class EventSource:
    """SSE (Server-Sent Events) client for TonConnect bridge."""

    def __init__(
        self,
        url: URL,
        session: aiohttp.ClientSession,
        headers: t.Optional[t.Dict[str, str]] = None,
        *,
        on_message: t.Callable[[EventMessage], t.Awaitable[None]],
        on_error: t.Callable[[Exception], t.Awaitable[None]],
    ) -> None:
        """
        :param url: SSE endpoint URL.
        :param session: HTTP session.
        :param headers: Extra request headers, or `None`.
        :param on_message: Async callback for received events.
        :param on_error: Async callback for errors.
        """
        self._url = url
        self._session = session
        self._headers = headers or {}

        self._on_message = on_message
        self._on_error = on_error

        self._decoder = EventDecoder()

        self._lock = asyncio.Lock()
        self._state = ReadyState.CLOSED

        self._resp: t.Optional[aiohttp.ClientResponse] = None
        self._task: t.Optional[asyncio.Task[None]] = None

    @property
    def ready_state(self) -> ReadyState:
        """Current connection state."""
        return self._state

    async def open(self, timeout: t.Optional[float] = None) -> None:
        """Open the SSE connection.

        :param timeout: Connection timeout in seconds, or `None`.
        """
        async with self._lock:
            if self._state != ReadyState.CLOSED:
                return
            self._state = ReadyState.CONNECTING

        resp: t.Optional[aiohttp.ClientResponse] = None
        try:
            req = self._session.get(
                self._url,
                headers={
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    **self._headers,
                },
            )
            resp = (
                await asyncio.wait_for(req, timeout=timeout)
                if timeout is not None
                else await req
            )
            assert resp is not None

            resp.raise_for_status()

            async with self._lock:
                if self._state == ReadyState.CLOSED:
                    return

                self._resp = resp
                self._decoder.reset()
                self._state = ReadyState.OPEN
                self._task = asyncio.create_task(self._loop())
                resp = None
        except asyncio.CancelledError:
            async with self._lock:
                self._state = ReadyState.CLOSED
            raise
        finally:
            if resp is not None:
                with suppress(Exception):
                    resp.close()

    async def close(self) -> None:
        """Close the SSE connection and cancel the read loop."""
        async with self._lock:
            if self._state == ReadyState.CLOSED:
                return

            self._state = ReadyState.CLOSED

            task, self._task = self._task, None
            resp, self._resp = self._resp, None
            self._decoder.reset()

        if task is not None and task is not asyncio.current_task():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        if resp is not None:
            with suppress(Exception):
                resp.close()

    async def _loop(self) -> None:
        """Read SSE stream, dispatch events, and handle errors."""
        exc: t.Optional[Exception] = None
        try:
            resp = self._resp
            if resp is None:
                return

            async for data in resp.content.iter_any():
                if self._state == ReadyState.CLOSED:
                    return

                for msg in self._decoder.feed(data):
                    try:
                        await self._on_message(msg)
                    except Exception as e:
                        with suppress(Exception):
                            await self._on_error(e)

            for msg in self._decoder.flush():
                try:
                    await self._on_message(msg)
                except Exception as e:
                    with suppress(Exception):
                        await self._on_error(e)

            exc = ConnectionError("EventSource connection closed")
        except asyncio.CancelledError:
            return
        except Exception as e:
            exc = e
        finally:
            if exc is not None:
                with suppress(Exception):
                    await self._on_error(exc)
            await self.close()
