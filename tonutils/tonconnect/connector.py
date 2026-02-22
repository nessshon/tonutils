import asyncio
import time
import typing as t
from enum import Enum

from tonutils.tonconnect.exceptions import (
    RequestTimeoutError,
    TonConnectError,
    TonConnectErrors,
    WalletAlreadyConnectedError,
    WalletNotConnectedError,
)
from tonutils.tonconnect.models import (
    Account,
    ActiveConnection,
    AppWallet,
    AppWallets,
    ConnectEventError,
    ConnectEventSuccess,
    ConnectItem,
    ConnectRequest,
    DisconnectEventError,
    DisconnectEventSuccess,
    RpcRequestBase,
    RpcResponseSuccessBase,
    SendTransactionPayload,
    SendTransactionResult,
    SendTransactionRpcRequest,
    SignDataPayload,
    SignDataResult,
    SignDataRpcRequest,
    TonAddressItem,
    TonProofItem,
    Wallet,
    WalletMessage,
    WalletResponseError,
    WalletResponseSuccess,
)
from tonutils.tonconnect.provider import Provider
from tonutils.tonconnect.provider.storage import ProviderStorage
from tonutils.tonconnect.utils import (
    verify_wallet_network,
    verify_send_transaction_support,
    verify_sign_data_support,
    verify_wallet_features,
    generate_universal_link,
    STANDARD_UNIVERSAL_LINK,
)
from tonutils.types import NetworkGlobalID

_ConnectResult = t.Tuple[
    t.Optional[Wallet],
    t.Optional[TonConnectError],
]
_SendTransactionResult = t.Tuple[
    t.Optional[SendTransactionResult],
    t.Optional[TonConnectError],
]
_SignDataResult = t.Tuple[
    t.Optional[SignDataResult],
    t.Optional[TonConnectError],
]
_RequestResult = t.Union[
    _SendTransactionResult,
    _SignDataResult,
]


class Event(str, Enum):
    """Events dispatched by `Connector`.

    Attributes:
        CONNECT: Wallet connection result.
        DISCONNECT: Wallet disconnection result.
        TRANSACTION: Send transaction result.
        SIGN_DATA: Sign data result.
        MESSAGE: Raw wallet message before processing.
        ERROR: Provider/bridge-level or unhandled handler error.
    """

    CONNECT = "connect"
    DISCONNECT = "disconnect"
    TRANSACTION = "transaction"
    SIGN_DATA = "sign_data"
    MESSAGE = "message"
    ERROR = "error"


class Connector:
    """TonConnect session connector managing wallet interactions."""

    DEFAULT_CONNECT_TIMEOUT: float = 15 * 60
    DEFAULT_REQUEST_TIMEOUT: float = 5 * 60

    def __init__(
        self,
        storage: ProviderStorage,
        session_key: str,
        manifest_url: str,
        app_wallets: AppWallets,
        handlers: t.Dict[Event, t.Callable[..., t.Awaitable[None]]],
        headers: t.Optional[t.Dict[str, str]] = None,
        context: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> None:
        """
        :param storage: Provider storage.
        :param session_key: Unique session key.
        :param manifest_url: URL to `tonconnect-manifest.json`.
        :param app_wallets: Wallet descriptors passed to the provider as bridge connection sources.
        :param handlers: Event handler mapping.
        :param headers: Extra HTTP headers, or `None`.
        :param context: User context dict, or `None`.
        """
        self._session_key = session_key
        self._manifest_url = manifest_url
        self._app_wallets = app_wallets
        self._handlers = handlers
        self._context: t.Dict[str, t.Any] = context or {}

        self._wallet: t.Optional[Wallet] = None
        self._network: t.Optional[NetworkGlobalID] = None

        self._connect_future: t.Optional[asyncio.Future[_ConnectResult]] = None
        self._connect_timeout_task: t.Optional[asyncio.Task[None]] = None

        self._request_futures: t.Dict[int, asyncio.Future[_RequestResult]] = {}
        self._request_timeout_tasks: t.Dict[int, asyncio.Task[None]] = {}
        self._request_events: t.Dict[int, Event] = {}

        self._storage = storage
        self._provider = Provider(
            storage=self._storage,
            app_wallets=app_wallets,
            on_message=self._on_message,
            on_error=self._on_provider_error,
            headers=headers,
        )

    def __getitem__(self, key: str) -> t.Any:
        return self._context[key]

    def __setitem__(self, key: str, value: t.Any) -> None:
        self._context[key] = value

    @property
    def session_key(self) -> str:
        """Unique session key."""
        return self._session_key

    @property
    def connected(self) -> bool:
        """Whether a wallet is currently connected."""
        return self._wallet is not None

    @property
    def storage(self) -> ProviderStorage:
        """Provider storage instance."""
        return self._storage

    @property
    def wallet(self) -> t.Optional[Wallet]:
        """Connected wallet, or `None`."""
        return self._wallet

    @property
    def account(self) -> t.Optional[Account]:
        """Connected wallet account, or `None`."""
        return self._wallet.account if self._wallet else None

    @property
    def app_wallet(self) -> t.Optional[AppWallet]:
        """Matched wallet app descriptor, or `None`."""
        bridge_url = self._provider.bridge_url
        if bridge_url is None:
            return None
        for w in self._app_wallets:
            if w.bridge_url == bridge_url:
                return w
        return None

    def make_connect_url(
        self,
        request: ConnectRequest,
        app_wallet: t.Optional[AppWallet] = None,
        redirect_url: t.Optional[str] = None,
    ) -> str:
        """Generate a universal link for a connect request.

        :param request: Connect request.
        :param app_wallet: Wallet descriptor for custom universal link, or `None`.
        :param redirect_url: Post-connect redirect URL, or `None`.
        :return: Link for connecting a wallet.
        """
        universal_link = STANDARD_UNIVERSAL_LINK
        if app_wallet is not None and app_wallet.universal_url:
            universal_link = app_wallet.universal_url

        return generate_universal_link(
            universal_link,
            message=request,
            session_id=self._provider.session_id,
            redirect_url=redirect_url,
        )

    def make_connect_request(
        self,
        ton_proof_payload: t.Optional[str] = None,
    ) -> ConnectRequest:
        """Build a `ConnectRequest` with standard items.

        :param ton_proof_payload: TON Proof challenge payload, or `None`.
        :return: Connect request.
        """
        items: t.List[ConnectItem] = [TonAddressItem()]
        if ton_proof_payload is not None:
            items.append(TonProofItem(payload=ton_proof_payload))
        return ConnectRequest(
            manifest_url=self._manifest_url,
            items=items,
        )

    async def connect(
        self,
        request: ConnectRequest,
        network: t.Optional[NetworkGlobalID] = None,
        app_wallet: t.Optional[AppWallet] = None,
        redirect_url: t.Optional[str] = None,
        timeout: t.Optional[float] = DEFAULT_CONNECT_TIMEOUT,
    ) -> str:
        """Initiate a wallet connection.

        :param request: Connect request.
        :param network: Expected network, or `None`.
        :param app_wallet: Wallet descriptor for custom universal link, or `None`.
        :param redirect_url: Post-connect redirect URL, or `None`.
        :param timeout: Connection timeout in seconds, or `None`.
        :return: Universal link for connecting a wallet.
        :raises WalletAlreadyConnectedError: If already connected.
        """
        if self.connected:
            raise WalletAlreadyConnectedError()
        self._cancel_connect()
        await self._provider.close_connection()
        await self._provider.connect(request)

        self._network = network
        loop = asyncio.get_running_loop()
        self._connect_future = loop.create_future()

        if timeout is not None:
            self._connect_timeout_task = asyncio.create_task(
                self._run_connect_timeout(timeout),
            )

        return self.make_connect_url(request, app_wallet, redirect_url=redirect_url)

    async def restore(self) -> bool:
        """Restore a connection from storage.

        :return: `True` if an active connection was restored.
        """
        connect_event = await self._provider.restore_connection()
        if connect_event is None:
            return False

        wallet = Wallet.from_payload(connect_event.payload)
        self._network = wallet.account.network
        self._wallet = wallet
        return True

    async def disconnect(self) -> None:
        """Disconnect the wallet.

        :raises WalletNotConnectedError: If no wallet is connected.
        """
        if not self.connected:
            raise WalletNotConnectedError()

        await self._provider.disconnect()
        self._wallet = None
        self._network = None
        self._cancel_all_requests()

    async def send_transaction(
        self,
        payload: SendTransactionPayload,
        timeout: t.Optional[float] = None,
    ) -> int:
        """Request the wallet to sign and send a transaction.

        :param payload: Transaction payload.
        :param timeout: Request timeout in seconds, or `None`.
        :return: Request ID for `wait_transaction`.
        """
        has_extra = any(m.extra_currency is not None for m in payload.messages)

        if self._wallet is not None:
            verify_send_transaction_support(
                self._wallet,
                len(payload.messages),
                app_wallet=self.app_wallet,
                has_extra_currency=has_extra,
            )

        if self._network is not None and payload.network is None:
            payload = payload.model_copy(update={"network": self._network})
        if self.account is not None and payload.from_address is None:
            payload = payload.model_copy(update={"from_address": self.account.address})

        if timeout is None and payload.valid_until is not None:
            timeout = max(payload.valid_until - int(time.time()), 0)
        if timeout is None:
            timeout = self.DEFAULT_REQUEST_TIMEOUT

        return await self._send_request(
            SendTransactionRpcRequest(params=[payload]),
            Event.TRANSACTION,
            timeout,
        )

    async def sign_data(
        self,
        payload: SignDataPayload,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ) -> int:
        """Request the wallet to sign arbitrary data.

        :param payload: Sign data payload.
        :param timeout: Request timeout in seconds, or `None`.
        :return: Request ID for `wait_sign_data`.
        """
        if self._wallet is not None:
            verify_sign_data_support(
                self._wallet,
                payload.type,
                app_wallet=self.app_wallet,
            )

        if self._network is not None and payload.network is None:
            payload = payload.model_copy(update={"network": self._network})
        if self.account is not None and payload.from_address is None:
            payload = payload.model_copy(update={"from_address": self.account.address})

        return await self._send_request(
            SignDataRpcRequest(params=[payload]),
            Event.SIGN_DATA,
            timeout,
        )

    async def wait_connect(self) -> _ConnectResult:
        """Await the pending connect result.

        :return: `(wallet, None)` on success, `(None, error)` on failure.
        :raises TonConnectError: If no connect request is pending.
        """
        if self._connect_future is None:
            raise TonConnectError("No pending connect request")
        try:
            return await self._connect_future
        finally:
            self._connect_future = None

    async def wait_transaction(self, request_id: int) -> _SendTransactionResult:
        """Await a pending send transaction result.

        :param request_id: Request ID from `send_transaction`.
        :return: `(result, None)` on success, `(None, error)` on failure.
        :raises TonConnectError: If request ID is unknown or not a transaction.
        """
        event = self._request_events.get(request_id)
        if event is not Event.TRANSACTION:
            raise TonConnectError(f"Request {request_id} is not a pending transaction")
        return await self._wait_request(request_id)

    async def wait_sign_data(self, request_id: int) -> _SignDataResult:
        """Await a pending sign data result.

        :param request_id: Request ID from `sign_data`.
        :return: `(result, None)` on success, `(None, error)` on failure.
        :raises TonConnectError: If request ID is unknown or not sign_data.
        """
        event = self._request_events.get(request_id)
        if event is not Event.SIGN_DATA:
            raise TonConnectError(f"Request {request_id} is not a pending sign_data")
        return await self._wait_request(request_id)

    async def drop_connect(self) -> None:
        """Cancel the pending connect request."""
        if self._connect_future is None:
            return
        self._cancel_connect_timeout()
        await self._provider.close_connection()
        if not self._connect_future.done():
            self._connect_future.cancel()
        self._connect_future = None

    def drop_request(self, request_id: int) -> None:
        """Cancel a pending request by ID.

        :param request_id: Request ID to cancel.
        """
        self._cancel_request_timeout(request_id)
        self._request_events.pop(request_id, None)
        future = self._request_futures.pop(request_id, None)
        if future is not None and not future.done():
            future.cancel()

    async def close(self) -> None:
        """Close all bridge connections without notifying the wallet."""
        self._cancel_connect()
        self._cancel_all_requests()
        await self._provider.close_connection()

    async def pause(self) -> None:
        """Pause SSE listening."""
        await self._provider.pause()

    async def unpause(self) -> None:
        """Resume SSE listening."""
        await self._provider.unpause()

    async def to_connection(self) -> t.Optional[ActiveConnection]:
        """Return the active connection from storage, or `None`."""
        try:
            conn = await self._storage.get_connection()
        except TonConnectError:
            return None
        return conn if isinstance(conn, ActiveConnection) else None

    async def _wait_request(self, request_id: int) -> _RequestResult:
        """Await a pending request result."""
        future = self._request_futures.get(request_id)
        if future is None:
            raise TonConnectError(f"Unknown request id: {request_id}")
        try:
            return await future
        finally:
            if request_id in self._request_futures:
                del self._request_futures[request_id]

    async def _emit_connect(self, error: t.Optional[TonConnectError]) -> None:
        """Resolve the connect future and dispatch the event."""
        self._cancel_connect_timeout()
        if self._connect_future is not None and not self._connect_future.done():
            self._connect_future.set_result((self._wallet, error))
        await self._dispatch(Event.CONNECT, error)

    async def _emit_request(
        self,
        request_id: int,
        result: t.Any,
        error: t.Optional[TonConnectError],
    ) -> None:
        """Resolve a request future and dispatch the event."""
        self._cancel_request_timeout(request_id)
        event = self._request_events.pop(request_id, None)
        future = self._request_futures.get(request_id)
        if future is not None and not future.done():
            future.set_result((result, error))
        if event is not None:
            await self._dispatch(event, request_id, result, error)

    async def _dispatch(self, event: Event, *args: t.Any) -> None:
        """Dispatch an event to its registered handler."""
        handler = self._handlers.get(event)
        if handler is None:
            return
        try:
            await handler(self, *args)
        except Exception as error:
            if event is not Event.ERROR:
                if not isinstance(error, TonConnectError):
                    error = TonConnectError(str(error))
                await self._dispatch(Event.ERROR, error)

    async def _send_request(
        self,
        request: RpcRequestBase,
        event: Event,
        timeout: t.Optional[float],
    ) -> int:
        """Encrypt, send, and register a pending request."""
        if not self.connected:
            raise WalletNotConnectedError()

        request_id = await self._provider.request(request)
        loop = asyncio.get_running_loop()

        self._request_futures[request_id] = loop.create_future()
        self._request_events[request_id] = event

        if timeout is not None:
            self._request_timeout_tasks[request_id] = asyncio.create_task(
                self._run_request_timeout(request_id, timeout),
            )

        return request_id

    async def _run_connect_timeout(self, timeout: float) -> None:
        """Fire connect timeout after delay."""
        try:
            await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            return
        self._connect_timeout_task = None
        await self._provider.close_connection()
        await self._emit_connect(RequestTimeoutError())

    async def _run_request_timeout(self, request_id: int, timeout: float) -> None:
        """Fire request timeout after delay."""
        try:
            await asyncio.sleep(timeout)
        except asyncio.CancelledError:
            return
        if request_id in self._request_timeout_tasks:
            del self._request_timeout_tasks[request_id]
        await self._emit_request(request_id, None, RequestTimeoutError())

    def _cancel_connect_timeout(self) -> None:
        """Cancel the connect timeout task."""
        if self._connect_timeout_task is not None:
            self._connect_timeout_task.cancel()
            self._connect_timeout_task = None

    def _cancel_connect(self) -> None:
        """Cancel the pending connect future and timeout."""
        self._cancel_connect_timeout()
        if self._connect_future is not None and not self._connect_future.done():
            self._connect_future.cancel()
        self._connect_future = None

    def _cancel_request_timeout(self, request_id: int) -> None:
        """Cancel the timeout task for a request."""
        task = self._request_timeout_tasks.pop(request_id, None)
        if task is not None:
            task.cancel()

    def _cancel_all_requests(self) -> None:
        """Cancel all pending request futures and timeouts."""
        for future in self._request_futures.values():
            if not future.done():
                future.cancel()
        self._request_futures.clear()
        for task in self._request_timeout_tasks.values():
            task.cancel()
        self._request_timeout_tasks.clear()
        self._request_events.clear()

    async def _on_provider_error(self, error: Exception) -> None:
        """Handle provider-level errors."""
        if not isinstance(error, TonConnectError):
            error = TonConnectError(str(error))
        await self._dispatch(Event.ERROR, error)

    async def _on_message(self, message: WalletMessage) -> None:
        """Route an incoming wallet message to the appropriate handler."""
        await self._dispatch(Event.MESSAGE, message)

        if isinstance(message, ConnectEventSuccess):
            await self._handle_connect_success(message)
        elif isinstance(message, ConnectEventError):
            await self._handle_connect_error(message)
        elif isinstance(message, DisconnectEventSuccess):
            await self._handle_disconnect_success(message)
        elif isinstance(message, DisconnectEventError):
            await self._handle_disconnect_error(message)
        elif isinstance(message, RpcResponseSuccessBase):
            await self._handle_response_success(message)
        elif isinstance(message, WalletResponseError):
            await self._handle_response_error(message)
        else:
            error = TonConnectError(f"Unsupported message: {message}")
            await self._dispatch(Event.ERROR, error)

    async def _handle_connect_success(self, message: ConnectEventSuccess) -> None:
        """Process a successful connect event."""
        wallet = Wallet.from_payload(message.payload)
        try:
            verify_wallet_features(wallet)
            if self._network is not None:
                verify_wallet_network(wallet, self._network)
        except TonConnectError as err:
            await self._storage.remove_connection()
            await self._provider.close_connection()
            await self._emit_connect(err)
            return

        self._wallet = wallet
        await self._emit_connect(None)

    async def _handle_connect_error(self, message: ConnectEventError) -> None:
        """Process a failed connect event."""
        error = TonConnectErrors.from_code(
            message.payload.code,
            message.payload.message,
        )
        await self._emit_connect(error)

    async def _handle_disconnect_success(self, _: DisconnectEventSuccess) -> None:
        """Process a successful disconnect event."""
        self._wallet = None
        self._cancel_all_requests()
        await self._storage.remove_connection()
        await self._provider.close_connection()
        self._cancel_connect_timeout()
        await self._dispatch(Event.DISCONNECT, None)

    async def _handle_disconnect_error(self, message: DisconnectEventError) -> None:
        """Process a failed disconnect event."""
        error = TonConnectErrors.from_code(
            message.payload.code,
            message.payload.message,
        )
        await self._dispatch(Event.DISCONNECT, error)

    async def _handle_response_success(self, message: WalletResponseSuccess) -> None:
        """Process a successful RPC response."""
        await self._emit_request(int(message.id), message.result, None)

    async def _handle_response_error(self, message: WalletResponseError) -> None:
        """Process a failed RPC response."""
        error = TonConnectErrors.from_code(
            message.error.code,
            message.error.message,
        )
        await self._emit_request(int(message.id), None, error)
