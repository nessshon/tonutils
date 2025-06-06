from __future__ import annotations

import asyncio
import inspect
import json
import time
from typing import List, Union, cast, Callable, Awaitable

from pytoniq_core import Address, Cell, StateInit

from .models import (
    Account,
    DeviceInfo,
    Event,
    EventError,
    Request,
    SendConnectRequest,
    SendDisconnectRequest,
    SendTransactionRequest,
    SendTransactionResponse,
    SignDataPayload,
    SignDataRequest,
    SignDataResponse,
    TonProof,
    Transaction,
    WalletApp,
    WalletInfo,
)
from .models.event import EventHandlers, EventHandlersData
from .provider.bridge import HTTPBridge
from .storage import IStorage
from .utils.exceptions import *
from .utils.logger import logger
from ..wallet.messages import TransferMessage


class Connector:
    """
    A class that serves as a high-level interface to connect to a wallet,
    send/receive transactions, and handle events such as CONNECT, DISCONNECT, and TRANSACTION.
    """

    SIGN_DATA_TIMEOUT = 300
    DISCONNECT_TIMEOUT = 600
    STANDARD_UNIVERSAL_URL = "tc://"

    class PendingRequestContext:
        """
        A context manager for awaiting an RPC request response.
        It retrieves the corresponding future from the connector’s pending_requests by ID.
        """

        def __init__(self, connector: Connector, rpc_request_id: int):
            """
            :param connector: The Connector instance.
            :param rpc_request_id: Unique RPC request ID used to identify the request.
            """
            self.connector = connector
            self.rpc_request_id = rpc_request_id

        async def __aenter__(self) -> Union[TonConnectError, SendTransactionResponse, SignDataResponse]:
            """
            Enters the context, returning the future’s result (either an error or a successful response).
            """
            future = self.connector.bridge.pending_requests.get(self.rpc_request_id)
            if future is None or future.done():
                logger.debug(f"No pending request with ID {self.rpc_request_id} found during request context entry")
                raise TonConnectError(f"No pending request with ID {self.rpc_request_id}")
            return await future

        async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
            """
            Exits the context without special handling for exceptions.
            """

    class ConnectWalletContext:
        """
        A context manager for awaiting a wallet connection response.
        It retrieves the corresponding future for the CONNECT event.
        """

        def __init__(self, connector: Connector):
            """
            :param connector: The Connector instance.
            """
            self.connector = connector

        async def __aenter__(self) -> Union[TonConnectError, WalletInfo]:
            """
            Enters the context, returning the future’s result (either an error or wallet info).
            """
            future = self.connector.bridge.pending_requests.get(self.connector.bridge.RESERVED_ID)
            if future is None or future.done():
                logger.debug("No pending wallet connection request found during connection context entry")
                raise TonConnectError("No pending wallet connection request found.")
            return await future

        async def __aexit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
            """
            Exits the context without special handling for exceptions.
            """

    def __init__(
            self,
            user_id: Union[int, str],
            manifest_url: str,
            storage: IStorage,
            api_tokens: Dict[str, str],
            on_events: EventHandlers,
            on_events_data: EventHandlersData,
            extra: Dict[str, Any],
    ) -> None:
        """
        Initializes the Connector.

        :param user_id: A unique user ID for distinguishing user sessions.
        :param manifest_url: The URL of the DApp manifest.
        :param storage: An IStorage implementation for saving and retrieving connection data.
        :param api_tokens: A dictionary of API tokens {api_name: token}.
        :param on_events: Handlers for specific events (connect, disconnect, transaction).
        :param on_events_data: Additional data passed to event handlers.
        :param extra: Other arguments that will be passed as keyword arguments to event handlers.
        """
        self.user_id = user_id

        self._manifest_url = manifest_url
        self._storage = storage
        self._api_tokens = api_tokens
        self._on_events = on_events
        self._events_data = on_events_data

        self._bridge: Optional[HTTPBridge] = None
        self._wallet: Optional[WalletInfo] = None
        self._wallet_app: Optional[WalletApp] = None
        self._connect_timeout_task: Optional[asyncio.Task] = None

        self.extra = extra

    @property
    def storage(self) -> IStorage:
        """
        :return: The IStorage instance used by the Connector.
        """
        return self._storage

    @property
    def connected(self) -> bool:
        """
        :return: True if a wallet is currently connected, False otherwise.
        """
        return self._wallet is not None

    @property
    def bridge(self) -> HTTPBridge:
        """
        :return: The active HTTPBridge instance, or None if not set.
        """
        return self._bridge  # type: ignore

    @property
    def wallet(self) -> Optional[WalletInfo]:
        """
        :return: The currently connected wallet’s info, or None if not connected.
        """
        return self._wallet if self.connected else None

    @property
    def account(self) -> Optional[Account]:
        """
        :return: The account associated with the connected wallet, or None if not connected.
        """
        return self._wallet.account if self._wallet else None

    @property
    def device(self) -> Optional[DeviceInfo]:
        """
        :return: The device info of the connected wallet, or None if not connected.
        """
        return self._wallet.device if self._wallet else None

    @property
    def proof(self) -> Optional[TonProof]:
        """
        :return: The TonProof data for the connected wallet, or None if not available.
        """
        return self._wallet.ton_proof if self._wallet else None

    @property
    def wallet_app(self) -> Optional[WalletApp]:
        """
        :return: The WalletApp object representing the wallet application data, if any.
        """
        return self._wallet_app

    def add_event_kwargs(self, event: Event, **kwargs) -> None:
        """
        Adds keyword arguments (data) to be passed to specific event handlers.

        :param event: The event identifier.
        :param kwargs: The data to store and pass to the event handler.
        """
        self._events_data[event].update(kwargs)
        event_error = getattr(EventError, event.name)
        self._events_data[event_error].update(kwargs)
        logger.debug(f"Added kwargs for event: {event.name} with data: {kwargs}")

    @staticmethod
    def _create_future() -> asyncio.Future:
        loop = asyncio.get_running_loop()
        return loop.create_future()

    def _clean_pending_request(self, rpc_request_id: int) -> None:
        if rpc_request_id in self.bridge.pending_requests:
            try:
                self.bridge.pending_requests[rpc_request_id].cancel()
                if rpc_request_id != -1:
                    logger.debug(f"Cancelled pending request with ID: {rpc_request_id}")
            except asyncio.CancelledError:
                if rpc_request_id != -1:
                    logger.debug(f"Attempted to cancel already cancelled request with ID: {rpc_request_id}")
            del self.bridge.pending_requests[rpc_request_id]
        if rpc_request_id in self.bridge.request_event_types:
            del self.bridge.request_event_types[rpc_request_id]

    async def _execute_event_handlers(self, handlers: List[Any], kwargs: Dict[str, Any]) -> None:
        """
        Executes the given list of event handlers, passing only the kwargs they accept.

        :param handlers: A list of callables (event handlers).
        :param kwargs: A dictionary of arguments to pass to each handler.
        """
        for handler in handlers:
            params = inspect.signature(handler).parameters
            filtered_kwargs = {k: v for k, v in {**self.extra, **kwargs}.items() if k in params}
            try:
                await handler(**filtered_kwargs)
                logger.debug(f"Executed handler: {handler.__name__} with args: {filtered_kwargs}")
            except Exception as e:
                logger.debug(f"Error executing handler {handler.__name__}: {e}")

    def _get_handlers_and_kwargs(
            self,
            event: Optional[Union[str, Event, EventError]] = None,
    ) -> tuple[List[Callable[..., Awaitable[None]]], Dict[str, Any]]:
        if event is None:
            return [], {}
        casted_event = cast(Union[Event, EventError], event)
        handlers = self._on_events.get(casted_event, []).copy()
        kwargs = self._events_data.get(casted_event, {}).copy()
        return handlers, kwargs

    async def _on_wallet_status_changed(self, response: Dict[str, Any]) -> None:
        """
        Internal callback triggered whenever a wallet status event occurs (CONNECT, DISCONNECT, etc.).

        :param response: A dictionary containing event info (e.g., event name, payload).
        """
        event, payload = response.get("event"), response.get("payload", {})
        logger.debug(f"Wallet status changed for user_id={self.user_id}: event={event}")
        handlers, kwargs = self._get_handlers_and_kwargs(event)
        kwargs["user_id"] = self.user_id

        if event == Event.CONNECT:
            self._wallet = WalletInfo.from_payload(payload)
            kwargs["wallet"] = self._wallet
            result = self._wallet
            logger.debug(f"Connected to wallet for user_id={self.user_id}")
        elif event == Event.DISCONNECT:
            kwargs["wallet"] = self._wallet
            await self.bridge.remove_session()
            self._wallet = result = None
            logger.debug(f"Disconnected from wallet for user_id={self.user_id}")
        else:
            error = ConnectEventError.from_response(response)
            kwargs["error"] = error
            result = error  # type: ignore
            logger.debug(f"Failed to connect to wallet for user_id={self.user_id}: {error}")

        await self._execute_event_handlers(handlers, kwargs)
        future = self.bridge.pending_requests.get(self.bridge.RESERVED_ID)

        if future and not future.done():
            future.set_result(result)
            self._clean_pending_request(self.bridge.RESERVED_ID)

    async def _on_rpc_response_received(self, response: Dict[str, Any], rpc_request_id: int) -> None:
        """
        Internal callback for handling RPC responses from the wallet.

        :param response: The response dictionary from the wallet/bridge.
        :param rpc_request_id: The unique ID correlating this response to a previous RPC request.
        """
        logger.debug(f"Received RPC response for user_id={self.user_id}: {response} (request ID: {rpc_request_id})")

        future = self.bridge.pending_requests.get(rpc_request_id)
        if future is None or future.done():
            logger.debug(f"Received RPC response for non-existent or completed request ID: {rpc_request_id}")
            return

        is_sign_data = self.bridge.request_event_types[rpc_request_id] == Event.SIGN_DATA
        error = SendRequestEventError.from_response(response)
        data: Dict[str, Any] = {"user_id": self.user_id}

        event: Union[Event, EventError]
        result: Union[SendTransactionResponse, SignDataResponse, TonConnectError]

        if error:
            event = EventError.SIGN_DATA if is_sign_data else EventError.TRANSACTION
            result = error
            data["error"] = error
            logger.debug(f"Request error for user_id={self.user_id}: {error}")
        elif is_sign_data:
            event = Event.SIGN_DATA
            sign_data = SignDataResponse.from_dict(response)
            result = sign_data
            data["sign_data"] = sign_data
            logger.debug(f"Sign Data successful for user_id={self.user_id}: {sign_data}")
        else:
            event = Event.TRANSACTION
            transaction = SendTransactionResponse.from_dict(response)
            result = transaction
            data["transaction"] = transaction
            logger.debug(f"Transaction successful for user_id={self.user_id}: {transaction.boc}")

        logger.debug(f"Processing event {event.name} for user_id={self.user_id}")
        handlers, kwargs = self._get_handlers_and_kwargs(event)
        kwargs.update(data)

        future.set_result(result)
        self._clean_pending_request(rpc_request_id)
        await self._execute_event_handlers(handlers, kwargs)

    def _prepare_transaction(self, transaction: Transaction) -> None:
        """
        Ensures the Transaction object is properly initialized before sending.
        Verifies the SendTransaction feature and sets default values.

        :param transaction: The Transaction object to be prepared.
        :raises TonConnectError: If the wallet is not connected or does not support SendTransaction.
        """
        if not self.wallet or not self.wallet.device:
            raise TonConnectError("Wallet or device info is not available.")
        self.wallet.device.verify_send_transaction_feature(self.wallet, len(transaction.messages))

        timestamp = int(time.time())
        transaction.valid_until = transaction.valid_until or timestamp + 300
        transaction.from_ = transaction.from_ or self._wallet.account.address.to_str()  # type: ignore
        transaction.network = transaction.network or self._wallet.account.chain  # type: ignore
        transaction.messages = transaction.messages or []

        logger.debug(
            "Transaction prepared for user_id=%d: valid_until=%d, from=%s, network=%s",
            self.user_id, transaction.valid_until, transaction.from_, transaction.network
        )

    async def _process_rpc_request(
            self,
            request: Request,
            connection: Dict[str, Any],
            rpc_request_id: int,
            timeout: int,
    ) -> None:
        connection["next_rpc_request_id"] = str(rpc_request_id + 1)
        await self.bridge.storage.set_item(self.storage.KEY_CONNECTION, json.dumps(connection))

        await asyncio.wait_for(
            asyncio.shield(
                self.bridge.send_request(
                    request=request,
                    rpc_request_id=rpc_request_id,
                ),
            ),
            timeout=timeout,
        )

    async def _process_transaction(
            self,
            transaction: Transaction,
            connection: Dict[str, Any],
            rpc_request_id: int,
    ) -> None:
        """
        Internal task to process (send) a transaction request and await the response.

        :param transaction: The Transaction object to be sent.
        :param connection: Stored connection data from IStorage.
        :param rpc_request_id: The unique RPC request ID for this transaction.
        """
        try:
            self.bridge.request_event_types[rpc_request_id] = Event.TRANSACTION

            self._prepare_transaction(transaction)
            request = SendTransactionRequest(params=[transaction])
            timeout = int(transaction.valid_until - int(time.time()))  # type: ignore

            await self._process_rpc_request(request, connection, rpc_request_id, timeout)

        except asyncio.TimeoutError:
            response = {"error": {"code": 500, "message": "Failed to send transaction: timeout."}}
            logger.debug(f"Transaction timeout for user_id={self.user_id} with request ID={rpc_request_id}")
            await self._on_rpc_response_received(response, rpc_request_id)

        except Exception as e:
            response = {"error": {"code": 0, "message": f"Failed to send transaction: {e}"}}
            logger.exception(
                "Unexpected error during transaction for user_id=%d with request ID=%d: %s",
                self.user_id, rpc_request_id, e
            )
            await self._on_rpc_response_received(response, rpc_request_id)

    async def _process_sign_data(
            self,
            payload: SignDataPayload,
            connection: Dict[str, Any],
            rpc_request_id: int,
    ) -> None:
        try:
            self.bridge.request_event_types[rpc_request_id] = Event.SIGN_DATA

            request = SignDataRequest(params=[payload])
            timeout = self.SIGN_DATA_TIMEOUT

            await self._process_rpc_request(request, connection, rpc_request_id, timeout)

        except asyncio.TimeoutError:
            response = {"error": {"code": 500, "message": "Failed to send sign data request: timeout."}}
            logger.debug(f"Sign data timeout for user_id={self.user_id} with request ID={rpc_request_id}")
            await self._on_rpc_response_received(response, rpc_request_id)

        except Exception as e:
            response = {"error": {"code": 0, "message": f"Failed to sign data: {e}"}}
            logger.exception(
                "Unexpected error during sign data for user_id=%d with request ID=%d: %s",
                self.user_id, rpc_request_id, e
            )
            await self._on_rpc_response_received(response, rpc_request_id)

    async def sign_data(self, payload: SignDataPayload) -> int:
        """
        Sends a sign data request to the wallet.

        :param payload: The payload to sign.
        :return: The RPC request ID for the sign data request.
        """
        if not self.wallet or not self.wallet.device:
            raise TonConnectError("Wallet or device info is not available.")

        self.wallet.device.verify_sign_data_feature(self.wallet, payload)
        logger.debug(f"Send Sign Data for user_id={self.user_id}: {payload}")

        connection = await self.bridge.get_stored_connection_data()  # type: ignore
        rpc_request_id = int(connection.get("next_rpc_request_id", "0"))
        self.bridge.pending_requests[rpc_request_id] = self._create_future()

        asyncio.create_task(self._process_sign_data(payload, connection, rpc_request_id))
        logger.debug(f"Send Sign Data task started for user_id={self.user_id} with request ID={rpc_request_id}")
        return rpc_request_id

    async def send_transaction(self, transaction: Transaction) -> int:
        """
        Public-facing method to send a transaction (or batch of messages).

        :param transaction: A Transaction object representing the transaction(s).
        :return: The RPC request ID associated with this transaction.
        :raises TonConnectError: If there's no active bridge session.
        """
        logger.debug(f"Sending transaction with {len(transaction.messages)} messages: {transaction.messages}")

        # Retrieve connection data to increment and store the next RPC request ID.
        connection = await self.bridge.get_stored_connection_data()  # type: ignore
        rpc_request_id = int(connection.get("next_rpc_request_id", "0"))
        self.bridge.pending_requests[rpc_request_id] = self._create_future()

        asyncio.create_task(self._process_transaction(transaction, connection, rpc_request_id))
        logger.debug(f"Transaction task started for user_id={self.user_id} with request ID={rpc_request_id}")
        return rpc_request_id

    async def connect_wallet(
            self,
            wallet_app: WalletApp,
            redirect_url: str = "back",
            ton_proof: Optional[str] = None,
    ) -> str:
        """
        Initiates the wallet connection process.

        :param wallet_app: The WalletApp object for the target wallet.
        :param redirect_url: The URL to which the user should be redirected after connecting.
        :param ton_proof: Optional proof data for TonConnect.
        :return: A universal link (URL) for the user to open in their wallet.
        :raises TonConnectError: If a wallet is already connected.
        """
        logger.debug(f"Initiating wallet connection for user_id={self.user_id} with app={wallet_app.name}")
        if self.connected:
            logger.debug(f"Wallet is already connected for user_id={self.user_id}")
            raise TonConnectError("A wallet is already connected.")

        if self._connect_timeout_task is not None and not self._connect_timeout_task.done():
            self._connect_timeout_task.cancel()
            logger.debug(f"Cancelled existing connect timeout task for user_id={self.user_id}")

        # Close any existing bridge session before creating a new one.
        if self.bridge:
            await self.bridge.close_connection()
            logger.debug(f"Closed existing bridge connection for user_id={self.user_id} before connecting new wallet")

        self._bridge = HTTPBridge(
            storage=self.storage,
            wallet_app=wallet_app,
            on_wallet_status_changed=self._on_wallet_status_changed,
            on_rpc_response_received=self._on_rpc_response_received,
            api_tokens=self._api_tokens,
        )
        self._wallet_app = wallet_app

        request = SendConnectRequest.create(self._manifest_url, ton_proof)
        universal_url = wallet_app.universal_url or self.STANDARD_UNIVERSAL_URL
        connect_url = await self.bridge.connect(
            request=request,
            universal_url=universal_url,
            redirect_url=redirect_url,
        )

        async def on_connect_timeout() -> None:
            """
            If the wallet is not connected within the default TTL, remove the session and raise an error event.
            """
            await asyncio.sleep(HTTPBridge.DEFAULT_TTL)
            if self.connected:
                return
            payload = {"code": 500, "message": "Failed to connect: timeout."}
            response = {"event": EventError.CONNECT, "payload": payload}
            logger.debug(f"Wallet connection timed out for user_id={self.user_id}")
            await self._on_wallet_status_changed(response)

        self.bridge.pending_requests[self.bridge.RESERVED_ID] = self._create_future()
        self._connect_timeout_task = asyncio.create_task(on_connect_timeout())

        logger.debug(f"Generated universal URL for user_id={self.user_id}: {connect_url}")
        return connect_url

    async def restore_connection(self) -> None:
        """
        Attempts to restore a previously established connection from storage.
        """
        logger.debug(f"Attempting to restore connection for user_id={self.user_id}")
        if self.bridge:
            await self.bridge.close_connection()
        else:
            self._bridge = HTTPBridge(
                storage=self.storage,
                wallet_app=None,
                on_wallet_status_changed=self._on_wallet_status_changed,
                on_rpc_response_received=self._on_rpc_response_received,
                api_tokens=self._api_tokens,
            )
        self._wallet = await self.bridge.restore_connection()
        self._wallet_app = self.bridge.wallet_app

    async def disconnect_wallet(self) -> None:
        """
        Initiates disconnection from the wallet and handles any required cleanup.

        :raises WalletNotConnectedError: If no wallet is currently connected.
        """
        logger.debug(f"Attempting to disconnect wallet for user_id={self.user_id}")
        if not self.connected:
            logger.debug(f"Attempted to disconnect a wallet while none is connected for user_id={self.user_id}")
            raise WalletNotConnectedError

        self.bridge.pending_requests[self.bridge.RESERVED_ID] = self._create_future()

        response: Dict[str, Any] = {"event": Event.DISCONNECT.value}
        try:
            await asyncio.wait_for(
                self.bridge.send_request(
                    request=SendDisconnectRequest(),
                    rpc_request_id=self.bridge.RESERVED_ID,
                ),
                timeout=self.DISCONNECT_TIMEOUT,
            )
            logger.debug(f"Wallet disconnected successfully for user_id={self.user_id}")
        except asyncio.TimeoutError:
            response = {
                "event": EventError.DISCONNECT,
                "payload": {"code": 500, "message": "Failed to disconnect: timeout."},
            }
            logger.debug(f"Timeout occurred while disconnecting the wallet for user_id={self.user_id}")
        finally:
            await self._on_wallet_status_changed(response)

    def connect_wallet_context(self) -> Connector.ConnectWalletContext:
        """
        Returns a context manager for awaiting the result of a CONNECT request.

        :return: A ConnectWalletContext instance.
        """
        return Connector.ConnectWalletContext(self)

    def cancel_connection_request(self) -> None:
        """
        Cancels a pending wallet connection request, removing it from the pending list.
        """
        future = self.bridge.pending_requests.get(self.bridge.RESERVED_ID)
        if future is not None and not future.done():
            future.cancel()
            logger.debug("Cancelled pending wallet connection request for user_id=%d", self.user_id)

        if self.bridge.RESERVED_ID in self.bridge.pending_requests:
            del self.bridge.pending_requests[self.bridge.RESERVED_ID]

        if self._connect_timeout_task is not None and not self._connect_timeout_task.done():
            self._connect_timeout_task.cancel()

    def is_request_pending(self, rpc_request_id: int) -> bool:
        """
        Checks if a particular request (by RPC request ID) is still pending.

        :param rpc_request_id: The ID of the request to check.
        :return: True if pending, otherwise False.
        """
        future = self.bridge.pending_requests.get(rpc_request_id)
        return future is not None and not future.done()

    def pending_request_context(self, rpc_request_id: int) -> Connector.PendingRequestContext:
        """
        Returns a context manager for awaiting the result of a pending request.

        :param rpc_request_id: The ID of the pending transaction.
        :return: A PendingRequestContext instance.
        """
        return Connector.PendingRequestContext(self, rpc_request_id)

    def cancel_pending_request(self, rpc_request_id: int) -> None:
        """
        Cancels a pending request by its RPC request ID, removing it from the pending list.

        :param rpc_request_id: The ID of the pending request to cancel.
        """
        future = self.bridge.pending_requests.get(rpc_request_id)
        if future is not None and not future.done():
            future.cancel()
            logger.debug(
                "Cancelled pending request for user_id=%d with request ID=%d",
                self.user_id, rpc_request_id
            )
        if rpc_request_id in self.bridge.pending_requests:
            del self.bridge.pending_requests[rpc_request_id]

    async def send_transfer(
            self,
            destination: Union[Address, str],
            amount: Union[float, int],
            body: Optional[Union[Cell, str]] = None,
            state_init: Optional[StateInit] = None,
    ) -> int:
        """
        Sends a single transfer to the given destination.

        :param destination: The transfer recipient (Address or string).
        :param amount: The amount in TON to transfer.
        :param body: An optional message body (Cell or string).
        :param state_init: An optional StateInit.
        :return: The RPC request ID for the transaction.
        """
        transaction = Transaction(messages=[Transaction.create_message(destination, amount, body, state_init)])
        request_id = await self.send_transaction(transaction)

        logger.debug(f"Transfer sent for user_id={self.user_id} with request ID={request_id}")
        return request_id

    async def send_batch_transfer(self, messages: List[TransferMessage]) -> int:
        """
        Sends multiple transfers (batch transaction) in one request.

        :param messages: A list of TransferMessage objects, each describing a transfer.
        :return: The RPC request ID for the batched transaction.
        """
        transaction = Transaction(messages=[Transaction.create_message(**data.__dict__) for data in messages])
        request_id = await self.send_transaction(transaction)

        logger.debug(f"Batch transfer sent for user_id={self.user_id} with request ID={request_id}")
        return request_id

    async def pause(self) -> None:
        """
        Pauses the SSE subscription (if any). The bridge will stop receiving wallet events until unpause.
        """
        if self.bridge:
            await self.bridge.pause_sse()
            logger.debug(f"SSE subscription paused for user_id={self.user_id}")

    async def unpause(self) -> None:
        """
        Resumes the SSE subscription by restarting the SSE listener (if any).
        """
        if self.bridge:
            await self.bridge.start_sse()
            logger.debug(f"SSE subscription resumed for user_id={self.user_id}")
