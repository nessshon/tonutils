from __future__ import annotations

import asyncio
import errno
from unittest.mock import AsyncMock, MagicMock

import pytest
from ton_core import LiteServerConfig, PrivateKey

from tonutils.exceptions import ProviderTimeoutError, TransportError
from tonutils.providers.lite.provider import LiteProvider
from tonutils.providers.lite.updater import UpdaterWorker
from tonutils.transports.adnl.tcp import AdnlTcpTransport

NODE = LiteServerConfig(ip="127.0.0.1", port=1, id=PrivateKey(bytes([1]) * 32).public_key.as_bytes)


def _connected_transport(drain_error: BaseException | None = None, closing: bool = False):
    transport = AdnlTcpTransport(NODE, connect_timeout=1)
    writer = MagicMock()
    writer.drain = AsyncMock(side_effect=drain_error)
    writer.wait_closed = AsyncMock()
    writer.transport.is_closing.return_value = closing
    transport.writer = writer
    transport.encrypt_frame = lambda data: data  # type: ignore[method-assign]
    transport._connected = True
    return transport, writer


class TestTransportConnectionLoss:
    async def test_socket_timeout_on_send_marks_transport_lost(self):
        transport, _ = _connected_transport(drain_error=TimeoutError(errno.ETIMEDOUT, "timed out"))
        with pytest.raises(TransportError):
            await transport.send_adnl_packet(b"payload")
        assert not transport.connected

    async def test_closing_transport_is_not_written_to(self):
        transport, writer = _connected_transport(closing=True)
        with pytest.raises(TransportError):
            await transport.send_adnl_packet(b"payload")
        writer.write.assert_not_called()
        assert not transport.connected


class TestProviderClose:
    async def test_pending_queries_fail_with_transport_error(self):
        provider = LiteProvider(NODE)
        provider.transport.close = AsyncMock()  # type: ignore[method-assign]
        fut: asyncio.Future[object] = asyncio.get_running_loop().create_future()
        provider.pending["query"] = fut

        await provider._do_close()

        assert not fut.cancelled()
        assert isinstance(fut.exception(), TransportError)


class TestUpdaterTimeouts:
    def _worker(self, *errors: BaseException) -> tuple[UpdaterWorker, MagicMock]:
        provider = MagicMock()
        provider.wait_masterchain_seqno = AsyncMock(side_effect=errors)
        worker = UpdaterWorker(provider)
        worker._last_mc_block = MagicMock(seqno=1)
        worker._running = True
        worker._task = asyncio.current_task()
        return worker, provider

    async def test_request_timeout_is_retried(self):
        worker, provider = self._worker(
            ProviderTimeoutError(timeout=1, endpoint=NODE.endpoint, operation="request"),
            RuntimeError("stop"),
        )
        with pytest.raises(RuntimeError):
            await worker._run()
        assert provider.wait_masterchain_seqno.await_count == 2

    async def test_bare_timeout_reaches_the_worker_wrapper(self):
        # Since Python 3.11 asyncio.TimeoutError is also a socket's ETIMEDOUT.
        worker, provider = self._worker(asyncio.TimeoutError(), RuntimeError("stop"))
        with pytest.raises(asyncio.TimeoutError):
            await worker._run()
        assert provider.wait_masterchain_seqno.await_count == 1
