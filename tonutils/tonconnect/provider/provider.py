import asyncio
import typing as t
from contextlib import suppress

from pydantic import TypeAdapter

from tonutils.tonconnect.exceptions import TonConnectError
from tonutils.tonconnect.models import (
    ActiveConnection,
    AppWallet,
    ConnectionSource,
    IncomingMessage,
    PendingConnection,
    BridgeProviderSession,
    ConnectEventSuccess,
    ConnectRequest,
    DisconnectEventSuccess,
    DisconnectRpcRequest,
    RpcRequestBase,
    SessionKeyPair,
    WalletMessage,
    EventBase,
    WalletResponse,
)
from tonutils.tonconnect.provider.gateway import Gateway, retry_until_success
from tonutils.tonconnect.provider.storage import ProviderStorage

_WALLET_MESSAGE_ADAPTER = TypeAdapter(WalletMessage)


class Provider:
    """Bridge-level provider managing SSE gateways and message routing."""

    SEND_TTL: int = 300
    SEND_ATTEMPTS: int = 10
    SEND_DELAY: float = 5.0

    CONNECT_ATTEMPTS: int = 10
    CONNECT_TIMEOUT: float = 12.0
    RECONNECT_DELAY: float = 2.0

    def __init__(
        self,
        *,
        storage: ProviderStorage,
        app_wallets: t.List[AppWallet],
        headers: t.Optional[t.Dict[str, str]] = None,
        on_message: t.Callable[[WalletMessage], t.Awaitable[None]],
        on_error: t.Callable[[Exception], t.Awaitable[None]],
    ) -> None:
        """
        :param storage: Provider storage.
        :param app_wallets: Wallet descriptors from which bridge connection sources are derived.
        :param headers: Extra HTTP headers, or `None`.
        :param on_message: Async callback for wallet messages.
        :param on_error: Async callback for errors.
        """
        self._storage = storage
        self._connection_sources = self._to_connection_sources(app_wallets)

        self._session_keypair = SessionKeyPair.generate()
        self._session_id = self._session_keypair.session_id

        self._headers = headers or {}
        self._on_message = on_message
        self._on_error = on_error

        self._gateway: t.Optional[Gateway] = None
        self._pending_gateways: t.List[Gateway] = []

        self._connect_lock = asyncio.Lock()

    @property
    def session_id(self) -> str:
        """Hex-encoded public key used as the SSE client ID."""
        return self._session_id

    @property
    def storage(self) -> ProviderStorage:
        """Provider storage instance."""
        return self._storage

    @property
    def bridge_url(self) -> t.Optional[str]:
        """Bridge URL of the active gateway, or `None`."""
        return self._gateway.bridge_url if self._gateway else None

    async def connect(self, request: ConnectRequest) -> None:
        """Store a pending connection and open SSE gateways.

        :param request: Connect request payload.
        """
        pending = PendingConnection(
            session_keypair=self._session_keypair,
            connect_request=request,
            connection_sources=self._connection_sources,
        )
        await self._storage.store_connection(pending)
        await self._open_gateways()

    async def request(self, request: RpcRequestBase) -> int:
        """Encrypt and send an RPC request to the wallet.

        :param request: RPC request to send.
        :return: Assigned request ID.
        :raises TonConnectError: If no active connection or gateway.
        """
        conn = await self._storage.get_connection()
        if not isinstance(conn, ActiveConnection):
            raise TonConnectError("Wallet is not connected")

        gw = self._gateway
        if gw is None:
            raise TonConnectError("Bridge gateway is not initialized")

        request_id = await self._storage.get_next_rpc_request_id()
        request.id = str(request_id)

        message = conn.session.session_keypair.encrypt(
            message=request.to_bytes(),
            receiver_public_key=conn.session.wallet_public_key,
        )
        await gw.send(
            message,
            conn.session.receiver,
            request.method,
            ttl=self.SEND_TTL,
            attempts=self.SEND_ATTEMPTS,
            delay=self.SEND_DELAY,
        )

        await self._storage.increase_next_rpc_request_id()
        return request_id

    async def disconnect(self) -> None:
        """Send a disconnect RPC (best-effort) and tear down the connection."""
        try:
            conn = await self._storage.get_connection()
        except TonConnectError:
            conn = None

        if isinstance(conn, ActiveConnection) and self._gateway is not None:
            request = DisconnectRpcRequest()

            with suppress(Exception):
                request_id = await self._storage.get_next_rpc_request_id()
                request.id = str(request_id)

                message = conn.session.session_keypair.encrypt(
                    message=request.to_bytes(),
                    receiver_public_key=conn.session.wallet_public_key,
                )
                await self._gateway.send(
                    message,
                    conn.session.receiver,
                    request.method,
                    ttl=self.SEND_TTL,
                    attempts=self.SEND_ATTEMPTS,
                    delay=self.SEND_DELAY,
                )

        await self._storage.remove_connection()
        await self.close_connection()

    async def restore_connection(self) -> t.Optional[ConnectEventSuccess]:
        """Restore a previously saved connection from storage.

        :return: Stored connect event on success, or `None`.
        """
        try:
            conn = await self._storage.get_connection()
        except TonConnectError:
            return None

        if isinstance(conn, PendingConnection):
            self._session_keypair = conn.session_keypair
            self._session_id = self._session_keypair.session_id
            await self._close_gateways()
            await self._open_gateways()
            return None

        if not isinstance(conn, ActiveConnection):
            return None

        self._session_keypair = conn.session.session_keypair
        self._session_id = self._session_keypair.session_id

        await self._close_gateways()

        self._gateway = Gateway(
            storage=self._storage,
            session_id=self._session_id,
            bridge_url=conn.session.bridge_url,
            headers=self._headers,
            on_gateway_message=self._on_gateway_message,
            on_gateway_error=self._on_gateway_error,
        )

        try:
            await retry_until_success(
                self._gateway.register_session,
                attempts=self.CONNECT_ATTEMPTS,
                delay=self.RECONNECT_DELAY,
            )
        except (Exception,):
            await self.close_connection()
            return None

        return conn.connect_event

    async def close_connection(self) -> None:
        """Close the active gateway and all pending gateways."""
        gw = self._gateway
        pending = list(self._pending_gateways)

        self._gateway = None
        self._pending_gateways = []

        if gw is not None:
            await gw.close()

        for pgw in pending:
            await pgw.close()

    async def pause(self) -> None:
        """Pause SSE listening on all gateways."""
        if self._gateway is not None:
            await self._gateway.pause()
        for gw in self._pending_gateways:
            await gw.pause()

    async def unpause(self) -> None:
        """Resume SSE listening on all gateways."""
        if self._gateway is not None:
            await self._gateway.unpause()
        for gw in self._pending_gateways:
            await gw.unpause()

    @staticmethod
    def _to_connection_sources(
        wallets: t.List[AppWallet],
    ) -> t.List[ConnectionSource]:
        """Convert wallet descriptors to connection sources."""
        return [
            ConnectionSource(
                bridge_url=wallet.bridge_url,
                universal_link=wallet.universal_url or "",
            )
            for wallet in wallets
            if wallet.bridge_url is not None
        ]

    async def _open_gateways(self) -> None:
        """Open SSE gateways for all connection sources."""
        await self.close_connection()

        for connection_source in self._connection_sources:
            gw = Gateway(
                storage=self._storage,
                session_id=self._session_id,
                bridge_url=connection_source.bridge_url,
                headers=self._headers,
                on_gateway_message=self._on_gateway_message,
                on_gateway_error=self._on_gateway_error,
            )
            self._pending_gateways.append(gw)

        if self._pending_gateways:
            tasks = [gw.register_session(timeout=2) for gw in self._pending_gateways]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            alive = []
            first_error: t.Optional[BaseException] = None
            for gw, result in zip(self._pending_gateways, results):
                if isinstance(result, BaseException):
                    if first_error is None:
                        first_error = result
                    await gw.close()
                else:
                    alive.append(gw)

            self._pending_gateways = alive

            if not self._pending_gateways and first_error is not None:
                raise first_error

    async def _close_gateways(self, *, exclude: t.Optional[Gateway] = None) -> None:
        """Close all pending gateways, optionally keeping one."""
        pending = list(self._pending_gateways)
        self._pending_gateways = []

        for pgw in pending:
            if pgw is not exclude:
                await pgw.close()

    async def _select_gateway(self, bridge_url: str) -> None:
        """Promote a pending gateway to active by bridge URL."""
        keep: t.Optional[Gateway] = None
        for gw in self._pending_gateways:
            if gw.bridge_url == bridge_url:
                keep = gw
                break

        if keep is None:
            return

        await self._close_gateways(exclude=keep)
        self._gateway = keep
        self._pending_gateways = []

    async def _on_gateway_error(self, exc: Exception) -> None:
        """Forward gateway errors to the error callback."""
        await self._on_error(exc)

    async def _on_gateway_message(
        self,
        msg: IncomingMessage,
        bridge_url: str,
    ) -> None:
        """Route an incoming gateway message to the handler."""
        try:
            await self._handle_message(msg, bridge_url)
        except Exception as exc:
            await self._on_error(exc)

    async def _handle_message(
        self,
        msg: IncomingMessage,
        bridge_url: str,
    ) -> None:
        """Decrypt, parse, and dispatch an incoming bridge message."""
        try:
            conn = await self._storage.get_connection()
        except TonConnectError:
            return

        if isinstance(conn, PendingConnection):
            session_keypair = conn.session_keypair
        elif isinstance(conn, ActiveConnection):
            session_keypair = conn.session.session_keypair
        else:
            return

        decrypted = session_keypair.decrypt(msg.message, msg.sender_public_key)

        wallet_msg = _WALLET_MESSAGE_ADAPTER.validate_json(decrypted)
        if isinstance(wallet_msg, WalletResponse):  # type: ignore[arg-type]
            await self._on_message(wallet_msg)
            return

        # Deduplicate wallet events by monotonic integer ID.
        if isinstance(wallet_msg, EventBase) and wallet_msg.id is not None:
            last_id = await self._storage.get_last_wallet_event_id()
            if last_id is not None and wallet_msg.id <= last_id:
                return

        # Lock to prevent race when multiple bridges deliver
        # ConnectEventSuccess concurrently.
        if isinstance(conn, PendingConnection) and isinstance(
            wallet_msg, ConnectEventSuccess
        ):
            async with self._connect_lock:
                try:
                    inner_conn = await self._storage.get_connection()
                except TonConnectError:
                    inner_conn = None

                if isinstance(inner_conn, PendingConnection):
                    active = ActiveConnection(
                        connect_event=wallet_msg,
                        next_rpc_request_id=0,
                        last_wallet_event_id=wallet_msg.id,
                        session=BridgeProviderSession(
                            session_keypair=session_keypair,
                            wallet_public_key=msg.sender_public_key,
                            bridge_url=bridge_url,
                        ),
                    )
                    await self._storage.store_connection(active)
                    await self._select_gateway(bridge_url)
                else:
                    return
        elif isinstance(wallet_msg, EventBase) and wallet_msg.id is not None:
            await self._storage.store_last_wallet_event_id(wallet_msg.id)

        if isinstance(wallet_msg, DisconnectEventSuccess):
            await self._storage.remove_connection()
            await self.close_connection()

        await self._on_message(wallet_msg)
