import asyncio
import base64
import typing as t
from contextlib import suppress

import aiohttp
from yarl import URL

from tonutils.tonconnect.exceptions import TonConnectError
from tonutils.tonconnect.models import IncomingMessage
from tonutils.tonconnect.provider.source import (
    EventMessage,
    EventSource,
    ReadyState,
)
from tonutils.tonconnect.provider.storage import ProviderStorage
from tonutils.tonconnect.utils import add_path_to_url

_T = t.TypeVar("_T")


async def retry_until_success(
    fn: t.Callable[[], t.Awaitable[_T]],
    *,
    attempts: int = 10,
    delay: float = 0.2,
) -> _T:
    """Retry an async callable until it succeeds.

    :param fn: Async callable to retry.
    :param attempts: Maximum number of attempts.
    :param delay: Delay between attempts in seconds.
    :return: Result of *fn*.
    :raises BaseException: Last exception if all attempts fail.
    """
    last_error: t.Optional[BaseException] = None

    for i in range(attempts):
        try:
            return await fn()
        except BaseException as exc:
            last_error = exc
            if i + 1 >= attempts:
                break
            await asyncio.sleep(delay)

    assert last_error is not None
    raise last_error


class Gateway:
    """SSE bridge gateway for a single TonConnect bridge connection."""

    SSE_PATH = "events"
    POST_PATH = "message"
    HEARTBEAT_MESSAGE = "heartbeat"

    RECONNECT_ATTEMPTS: int = 5
    RECONNECT_DELAY: float = 2.0

    def __init__(
        self,
        *,
        session_id: str,
        bridge_url: str,
        storage: ProviderStorage,
        headers: t.Optional[t.Dict[str, str]] = None,
        on_gateway_message: t.Callable[[IncomingMessage, str], t.Awaitable[None]],
        on_gateway_error: t.Callable[[Exception], t.Awaitable[None]],
    ) -> None:
        """
        :param session_id: SSE client identifier.
        :param bridge_url: Bridge base URL.
        :param storage: Provider storage.
        :param headers: Extra HTTP headers, or `None`.
        :param on_gateway_message: Async callback for incoming messages.
        :param on_gateway_error: Async callback for errors.
        """
        self._session_id = session_id
        self._bridge_url = bridge_url
        self._storage = storage

        self._headers = headers or {}
        self._on_gateway_message = on_gateway_message
        self._on_gateway_error = on_gateway_error

        self._http_session: t.Optional[aiohttp.ClientSession] = None
        self._event_source: t.Optional[EventSource] = None

        self._connect_lock = asyncio.Lock()
        self._reconnect_task: t.Optional[asyncio.Task[None]] = None

        self._closed = False
        self._paused = False

    @property
    def bridge_url(self) -> str:
        """Bridge URL this gateway is connected to."""
        return self._bridge_url

    @property
    def ready_state(self) -> ReadyState:
        """Current SSE connection state."""
        if self._closed:
            return ReadyState.CLOSED
        es = self._event_source
        if es is None:
            return ReadyState.CLOSED
        return es.ready_state

    async def register_session(self, timeout: float = 12.0) -> None:
        """Open an SSE session with the bridge.

        :param timeout: Connection timeout in seconds.
        :raises TonConnectError: If the gateway is closed.
        """
        if self._closed:
            raise TonConnectError("Bridge is closed")
        if self._paused:
            return

        async with self._connect_lock:
            if self._closed or self._paused:
                return

            state = self.ready_state
            if state in (ReadyState.OPEN, ReadyState.CONNECTING):
                return

            await self._close_event_source()

            last_event_id = await self._storage.get_last_event_id()
            url = self._make_open_url(last_event_id)
            session = await self._ensure_session()
            es = EventSource(
                session=session,
                url=url,
                headers=self._headers,
                on_message=self._on_event_source_message,
                on_error=self._on_event_source_error,
            )
            self._event_source = es

            try:
                await es.open(timeout)
            except BaseException:
                await self._close_event_source()
                raise

    async def send(
        self,
        message: bytes,
        receiver: str,
        topic: str,
        *,
        ttl: int = 300,
        attempts: int = 10,
        delay: float = 5.0,
    ) -> None:
        """Send an encrypted message to a wallet via the bridge.

        :param message: Encrypted message bytes.
        :param receiver: Hex-encoded wallet public key.
        :param topic: Bridge topic (RPC method name).
        :param ttl: Message time-to-live in seconds.
        :param attempts: Retry attempts for the HTTP POST.
        :param delay: Delay between retries in seconds.
        :raises TonConnectError: If the gateway is closed or send fails.
        """
        if self._closed:
            raise TonConnectError("Bridge is closed")

        url = self._make_send_url(
            receiver=receiver,
            topic=topic,
            ttl=ttl,
        )
        body = base64.b64encode(message).decode()

        async def _post_once() -> None:
            session = await self._ensure_session()
            async with session.post(str(url), data=body) as resp:
                if resp.status < 200 or resp.status >= 300:
                    raise TonConnectError(f"Bridge send failed, status {resp.status}")

        await retry_until_success(
            _post_once,
            attempts=attempts,
            delay=delay,
        )

    async def pause(self) -> None:
        """Pause SSE listening and cancel any pending reconnect."""
        self._paused = True

        task, self._reconnect_task = self._reconnect_task, None
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await task

        await self._close_event_source()

    async def unpause(self) -> None:
        """Resume SSE listening after a pause."""
        if self._closed or not self._paused:
            return
        self._paused = False
        await self.register_session()

    async def close(self) -> None:
        """Permanently close the gateway and release resources."""
        self._closed = True
        self._paused = True

        task, self._reconnect_task = self._reconnect_task, None
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError, Exception):
                await task

        await self._close_event_source()
        await self._close_session()

    async def _reconnect(self) -> None:
        """Schedule automatic reconnection with retries."""
        if self._closed or self._paused:
            return

        task = self._reconnect_task
        if task is not None and not task.done():
            return

        async def _runner() -> None:
            await self._close_event_source()
            await asyncio.sleep(self.RECONNECT_DELAY)
            if self._closed or self._paused:
                return
            try:
                await retry_until_success(
                    self.register_session,
                    attempts=self.RECONNECT_ATTEMPTS,
                    delay=self.RECONNECT_DELAY,
                )
            except Exception as exc:
                if not self._closed and not self._paused:
                    with suppress(Exception):
                        err = TonConnectError(
                            f"Bridge reconnect failed after "
                            f"{self.RECONNECT_ATTEMPTS} attempts: {exc}"
                        )
                        await self._on_gateway_error(err)

        task = asyncio.create_task(_runner())
        self._reconnect_task = task

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Return the HTTP session, creating one if needed."""
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(
                    total=None,
                    sock_connect=30,
                    sock_read=None,
                ),
            )
        return self._http_session

    async def _close_event_source(self) -> None:
        """Close and discard the current `EventSource`."""
        es, self._event_source = self._event_source, None
        if es is None:
            return
        with suppress(Exception):
            await es.close()

    async def _close_session(self) -> None:
        """Close and discard the HTTP session."""
        session, self._http_session = self._http_session, None
        if session is None:
            return
        with suppress(Exception):
            await session.close()

    async def _on_event_source_error(self, exc: Exception) -> None:
        """Handle SSE-level errors, triggering reconnect as needed."""
        if self._closed or self._paused:
            return

        state = self.ready_state
        if state == ReadyState.CONNECTING:
            with suppress(Exception):
                err = TonConnectError("Bridge error, failed to connect")
                await self._on_gateway_error(err)
            await self._reconnect()
            return

        if state == ReadyState.OPEN:
            with suppress(Exception):
                await self._on_gateway_error(exc)
            return

        await self._reconnect()

    async def _on_event_source_message(self, e: EventMessage) -> None:
        """Handle a raw SSE event, parsing and dispatching it."""
        if e.data is None or e.data == self.HEARTBEAT_MESSAGE:
            return
        if e.event_id:
            await self._storage.store_last_event_id(e.event_id)

        if self._closed or self._paused:
            return

        try:
            msg = IncomingMessage.model_validate_json(e.data)
        except Exception as exc:
            with suppress(Exception):
                err = TonConnectError(
                    f"Bridge message parse failed, "
                    f"message: `{e.data}`, "
                    f"error: {exc}"
                )
                await self._on_gateway_error(err)
            return

        try:
            await self._on_gateway_message(msg, self._bridge_url)
        except Exception as exc:
            with suppress(Exception):
                await self._on_gateway_error(exc)

    def _make_open_url(self, last_event_id: t.Optional[str] = None) -> URL:
        """Build the SSE endpoint URL."""
        query: t.Dict[str, str] = {"client_id": self._session_id}
        if last_event_id:
            query["last_event_id"] = last_event_id
        base = add_path_to_url(self._bridge_url, self.SSE_PATH)
        return URL(base).with_query(query)

    def _make_send_url(self, receiver: str, topic: str, ttl: int) -> URL:
        """Build the POST endpoint URL for sending messages."""
        query: t.Dict[str, str] = {
            "client_id": self._session_id,
            "to": receiver,
            "ttl": str(ttl),
            "topic": topic,
        }
        base = add_path_to_url(self._bridge_url, self.POST_PATH)
        return URL(base).with_query(query)
