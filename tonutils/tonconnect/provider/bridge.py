import asyncio
import json
from typing import Awaitable, Callable, Dict, Optional, Any
from urllib.parse import urlencode, quote_plus

import aiohttp

from ..models import (
    Request,
    SendConnectRequest,
    SendDisconnectRequest,
    WalletApp,
    WalletInfo,
    Event
)
from ..provider.session import BridgeSession, SessionCrypto
from ..storage import IStorage
from ..utils.exceptions import TonConnectError
from ..utils.logger import logger


class HTTPBridge:
    """
    A class responsible for interacting with TonConnect via an HTTP-based bridge.
    It provides:
    - URL generation for SSE subscription and POST requests,
    - Receiving and processing SSE events,
    - Sending requests (RPC and connect/disconnect).
    """

    SSE_PATH = "events"
    POST_PATH = "message"
    DEFAULT_TTL = 300
    RESERVED_ID = -1

    def __init__(
            self,
            storage: IStorage,
            on_wallet_status_changed: Callable[..., Awaitable],
            on_rpc_response_received: Callable[..., Awaitable],
            api_tokens: Dict[str, str],
            wallet_app: Optional[WalletApp] = None,
    ) -> None:
        """
        :param storage: Interface for data storage.
        :param on_wallet_status_changed: Callback triggered when wallet status changes.
        :param on_rpc_response_received: Callback triggered when an RPC response is received.
        :param api_tokens: Dictionary of API tokens, where the key is the API name, and the value is the token.
        :param wallet_app: Optional wallet application data.
        """
        self.storage: IStorage = storage
        self.api_tokens = api_tokens
        self.wallet_app: Optional[WalletApp] = wallet_app

        # Manages current session data, cryptographic objects, etc.
        self.session = BridgeSession()
        # Holds futures by request ID so that we can retrieve the corresponding future upon response.
        self.pending_requests: Dict[int, asyncio.Future] = {}

        self._api_token: Optional[str] = self._choose_api_token(api_tokens, wallet_app)
        self._on_wallet_status_changed = on_wallet_status_changed
        self._on_rpc_response_received = on_rpc_response_received

        self._is_closed = False
        self._event_task: Optional[asyncio.Task] = None
        self._client_session: Optional[aiohttp.ClientSession] = None

    @property
    def closed(self) -> bool:
        """
        Indicates whether the bridge has been closed (i.e., it no longer processes events).
        """
        return self._is_closed

    @property
    def client_session_closed(self) -> bool:
        """
        Checks whether the current aiohttp client session is closed.
        """
        if not self._client_session:
            return True
        return self._client_session.closed

    @staticmethod
    def _choose_api_token(
            api_tokens: Dict[str, str],
            wallet_app: Optional[WalletApp] = None
    ) -> Optional[str]:
        """
        Selects the appropriate API token based on the wallet bridge URL.

        :param api_tokens: A dictionary {bridge_name: token}.
        :param wallet_app: WalletApp object containing the bridge URL.
        :return: The matching token or None if no match is found.
        """
        if not wallet_app:
            return None

        bridge_url = wallet_app.bridge_url or ""
        api_token = next((token for name, token in api_tokens.items() if name in bridge_url), None)

        if api_token is None:
            logger.debug(f"No matching API token found for bridge: {bridge_url}")
        else:
            logger.debug(f"Selected API token '{api_token}' for bridge: {bridge_url}")

        return api_token

    def _build_url(self, path: str, params: dict) -> str:
        """
        Constructs a full URL by appending query parameters to the base wallet_app bridge URL.

        :param path: An endpoint path (e.g., "events" or "message").
        :param params: A dictionary of query parameters.
        :return: The constructed URL as a string.
        """
        query_string = urlencode(params)
        return f"{self.wallet_app.bridge_url}/{path}?{query_string}"  # type: ignore

    def _build_post_url(
            self,
            to: str,
            topic: Optional[str] = None,
            ttl: Optional[int] = None
    ) -> str:
        """
        Constructs a URL for sending a POST request to the bridge.

        :param to: The recipient’s public key.
        :param topic: The topic of the message (used for RPC methods).
        :param ttl: The message's time-to-live.
        :return: The constructed URL.
        """
        params = {
            "client_id": self.session.session_crypto.session_id,
            "to": to,
            "ttl": ttl or self.DEFAULT_TTL,
            "topic": topic,
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._build_url(self.POST_PATH, params)

    def _build_sse_url(self, last_event_id: Optional[str] = None) -> str:
        """
        Constructs a URL for subscribing to SSE events.

        :param last_event_id: The ID of the last processed event (for resuming).
        :return: The constructed SSE subscription URL.
        """
        params = {"client_id": self.session.session_crypto.session_id}
        if last_event_id is not None:
            params["last_event_id"] = last_event_id
        return self._build_url(self.SSE_PATH, params)

    @staticmethod
    def _is_telegram_url(url: str) -> bool:
        """
        Checks if a URL is a Telegram link (tg:// or t.me).

        :param url: The URL to check.
        :return: True if it's a Telegram URL, False otherwise.
        """
        return "tg" in url or "t.me" in url

    @staticmethod
    def _encode_telegram_params(params: str) -> str:
        """
        Encodes query parameters for a Telegram URL using the 'startapp' format.

        :param params: The raw query params as a string.
        :return: The encoded Telegram-specific string.
        """
        startapp = (
                "tonconnect-"
                + params
                .replace("+", "")
                .replace(".", "%2E")
                .replace("-", "%2D")
                .replace("_", "%5F")
                .replace("=", "__")
                .replace("&", "-")
                .replace("%", "--")
                .replace(":", "--3A")
                .replace("/", "--2F")
        )
        return f"startapp={startapp}"

    async def _process_event_data(self, raw_event: str) -> None:
        try:
            incoming_data = json.loads(raw_event)
            logger.debug(f"Parsed SSE event data: {incoming_data}")
        except json.JSONDecodeError:
            logger.debug("Failed to decode SSE data. Skipping.")
            return

        message = incoming_data.get("message")
        sender_pub_key = incoming_data.get("from")

        if not message or not sender_pub_key:
            logger.debug("Incomplete SSE data received. Missing 'message' or 'from'.")
            return

        decrypted_message = self.session.session_crypto.decrypt(
            message=message,
            sender_pub_key=sender_pub_key,
        )
        try:
            incoming_message = json.loads(decrypted_message)
            logger.debug(f"Decrypted incoming message: {incoming_message}")
            await self._handle_incoming_message(incoming_message, sender_pub_key)
        except json.JSONDecodeError:
            logger.debug("Decrypted message is not valid JSON. Skipping.")
            return

    async def _subscribe_to_events(self, url: str) -> None:
        """
        Subscribes to SSE events at the given URL and processes incoming messages.

        :param url: The SSE subscription URL.
        """
        logger.debug(f"Attempting to subscribe to SSE events at URL: {url}")
        max_retries, retry_count, retry_delay = 5, 0, 5

        while not self._is_closed:
            if not self._client_session:
                timeout = aiohttp.ClientTimeout(total=-1)
                headers = {"Authorization": f"Bearer {self._api_token}"} if self._api_token else {}
                self._client_session = aiohttp.ClientSession(headers=headers, timeout=timeout)

            try:
                async with self._client_session.get(url) as response:
                    if response.status != 200:
                        logger.debug(f"Failed to connect to bridge with status code: {response.status}")
                        raise TonConnectError(f"Failed to connect to bridge: {response.status}")

                    logger.debug("Connected to SSE stream successfully.")
                    async for line in response.content:
                        if self._is_closed:
                            logger.debug("SSE subscription closed by user.")
                            break

                        decoded_line = line.decode().strip()
                        if decoded_line.startswith("id:"):
                            event_id = decoded_line[3:].strip()
                            await self.storage.set_item(self.storage.KEY_LAST_EVENT_ID, event_id)
                        if decoded_line.startswith("data:"):
                            raw_event = decoded_line[5:].strip()
                            if raw_event:
                                await self._process_event_data(raw_event)

                    # Reset retry counter upon successful connection
                    retry_count = 0

            except (aiohttp.ClientPayloadError, RuntimeError) as e:
                if self._is_closed:
                    logger.debug("SSE subscription closed by user.")
                    break

                retry_count += 1
                logger.debug(f"Connection issue: {e}. Retrying in 5 seconds ({retry_count}/{max_retries})...")
                await asyncio.sleep(retry_delay)

                if retry_count >= max_retries:
                    logger.debug("Max retries reached. Sending disconnect event.")
                    await self._on_wallet_status_changed(SendDisconnectRequest().to_dict())
                    await self.remove_session()
                    break

            except asyncio.CancelledError:
                logger.debug("SSE subscription task was cancelled.")
                break
            except Exception as e:
                logger.exception(f"Unexpected error during SSE subscription: {e}")
                break

        logger.debug("SSE subscription task completed.")
        await self.pause_sse()

    async def _handle_incoming_message(
            self,
            incoming_message: Dict[str, Any],
            sender_pub_key: Optional[str] = None,
    ) -> None:
        """
        Handles a decrypted, parsed incoming message.

        :param incoming_message: The decrypted message as a dictionary.
        :param sender_pub_key: The sender’s public key, if available.
        """
        event_id = incoming_message.get("id")
        event_name = incoming_message.get("event")

        # Convert event_id to an integer if it's a string
        if isinstance(event_id, str):
            try:
                event_id = int(event_id)
            except ValueError:
                event_id = None
                logger.debug(f"Invalid event ID format: {incoming_message.get('id')}")

        connection = await self.get_stored_connection_data()
        last_wallet_event_id = connection.get("last_wallet_event_id")

        # If this is an RPC response (no 'event' field set)
        if event_name is None:
            future = self.pending_requests.get(event_id)  # type: ignore
            logger.debug(f"Received RPC response for event ID {event_id}")
            if future is not None and not future.done():
                await self._on_rpc_response_received(incoming_message, event_id)
            return

        # It's a CONNECT or DISCONNECT event
        if event_id is not None:
            # Prevent reprocessing older events (except for CONNECT)
            if last_wallet_event_id is not None and event_id <= last_wallet_event_id:
                logger.debug(f"Ignoring older event ID {event_id} <= {last_wallet_event_id}")
                return
            if event_name != Event.CONNECT:
                connection["last_wallet_event_id"] = event_id
                await self.storage.set_item(self.storage.KEY_CONNECTION, json.dumps(connection))

        if event_name == Event.CONNECT:
            if sender_pub_key:
                await self.update_session(incoming_message, sender_pub_key)
        elif event_name == Event.DISCONNECT:
            await self.remove_session()

        await self._on_wallet_status_changed(incoming_message)

    async def _send(
            self,
            request: str,
            receiver_public_key: str,
            topic: Optional[str] = None,
            ttl: Optional[int] = None,
    ) -> None:
        """
        Sends an encrypted message to the bridge via HTTP POST.

        :param request: The encrypted request string.
        :param receiver_public_key: The recipient’s public key (used in the URL).
        :param topic: Used in the query params (e.g., for RPC method).
        :param ttl: The time-to-live of the message on the bridge.
        """
        url = self._build_post_url(receiver_public_key, topic, ttl)
        headers = {"Authorization": f"Bearer {self._api_token}"} if self._api_token else {}

        logger.debug(f"Sending POST request to URL: {url}")
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                headers = {"Content-type": "text/plain;charset=UTF-8"}
                async with session.post(url, data=request, headers=headers) as response:
                    if response.status != 200:
                        logger.debug(f"Failed to send message with status code: {response.status}")
                        raise TonConnectError(f"Failed to send message: {response.status}")
            except aiohttp.ClientError as e:
                logger.exception(f"HTTP Client Error while sending message: {e}")
                raise TonConnectError(f"HTTP Client Error: {e}")

    async def start_sse(self) -> None:
        """
        Starts the SSE subscription. Cancels any existing subscription task if present.
        """
        if self._is_closed:
            logger.debug("Attempted to start SSE while bridge is closed")
            return

        last_event_id = await self.storage.get_item(self.storage.KEY_LAST_EVENT_ID)
        url = self._build_sse_url(last_event_id)

        if self._event_task:
            self._event_task.cancel()
            try:
                await self._event_task
                logger.debug("Previous SSE task completed")
            except asyncio.CancelledError:
                logger.debug("Previous SSE task cancelled")

        self._event_task = asyncio.create_task(self._subscribe_to_events(url))

    async def pause_sse(self) -> None:
        """
        Pauses SSE subscription by closing the aiohttp session and canceling the SSE task.
        """
        logger.debug("Pausing SSE subscription")
        if self._client_session:
            await self._client_session.close()
            self._client_session = None
            logger.debug("aiohttp ClientSession closed for SSE subscription")

        if self._event_task and not self._event_task.done():
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass
        self._event_task = None

    async def send_request(
            self,
            request: Request,
            rpc_request_id: int,
    ) -> Any:
        """
        Sends an RPC request to the wallet. Optionally waits for the response using a Future.

        :param request: A request object (Request or its subclasses).
        :param rpc_request_id: A unique ID to correlate requests and responses.
        :return: The response result if available, or None.
        """
        if not self.session or not self.session.wallet_public_key:
            logger.debug("Trying to send a request without an active session.")
            raise TonConnectError("Trying to send a request without an active session.")

        request.id = rpc_request_id
        message = json.dumps(request.to_dict())

        encoded_request = self.session.session_crypto.encrypt(
            message=message,
            receiver_pub_key=self.session.wallet_public_key,
        )
        await self._send(
            request=encoded_request,
            receiver_public_key=self.session.wallet_public_key,
            topic=request.method,
        )

        if rpc_request_id == self.RESERVED_ID:
            logger.debug("Reserved request ID used; no future to set.")
            return

        logger.debug(f"Request ID {rpc_request_id} sent successfully. Waiting for response...")
        future = self.pending_requests.get(rpc_request_id)
        return await future if future else None

    async def get_stored_connection_data(self) -> Dict[str, Any]:
        """
        Retrieves stored session data from the storage.

        :return: A dictionary containing the connection data.
        """
        connection = await self.storage.get_item(self.storage.KEY_CONNECTION, "{}")
        return json.loads(connection)  # type: ignore

    def generate_universal_url(
            self,
            request: Dict[str, Any],
            universal_url: str,
            redirect_url: str,
    ) -> str:
        """
        Generates a universal link for initiating a connection (e.g., for Telegram or another wallet).

        :param request: A dictionary containing the connect request data.
        :param universal_url: The base wallet universal URL.
        :param redirect_url: The URL to redirect the user back to after the action (e.g., "back").
        :return: The constructed universal link as a string.
        """
        version = 2
        session_id = self.session.session_crypto.session_id
        request_safe = quote_plus(json.dumps(request, separators=(",", ":")))
        query_params = f"v={version}&id={session_id}&r={request_safe}&ret={redirect_url}"

        if self._is_telegram_url(universal_url):
            # If it's a Telegram URL, convert the universal_url and query
            universal_url = WalletApp.universal_url_to_direct_url(universal_url)
            query_params = self._encode_telegram_params(query_params)
            return f"{universal_url}?{query_params}"

        return f"{universal_url}?{query_params}"

    async def connect(
            self,
            request: SendConnectRequest,
            universal_url: str,
            redirect_url: str = "back",
    ) -> str:
        """
        Initiates a connection (CONNECT):
        - Generates a new session,
        - Builds a universal link,
        - Starts the SSE subscription.

        :param request: The connect request object.
        :param universal_url: The wallet’s base universal link.
        :param redirect_url: The back URL (defaults to "back").
        :return: The final connect URL to be opened by the user.
        """
        await self.close_connection()

        session_crypto = SessionCrypto()
        self.session.bridge_url = self.wallet_app.bridge_url if self.wallet_app else ""
        self.session.session_crypto = session_crypto

        connect_url = self.generate_universal_url(
            request=request.to_dict(),
            universal_url=universal_url,
            redirect_url=redirect_url,
        )
        await self.start_sse()

        return connect_url

    async def restore_connection(self) -> WalletInfo:
        """
        Restores a previously established connection from storage (if CONNECT was previously called).

        :return: A WalletInfo object with the restored wallet data.
        :raises TonConnectError: If restoration fails due to missing or invalid data.
        """
        stored_connection = await self.storage.get_item(self.storage.KEY_CONNECTION)
        if not stored_connection:
            raise TonConnectError("Restore failed: no connection data found in storage.")

        connection = json.loads(stored_connection)
        if "session" not in connection:
            raise TonConnectError("Restore failed: no session data found in storage.")

        # Rebuild the session from stored data
        self.session = BridgeSession(stored=connection["session"])
        if self.session.bridge_url is None:
            raise TonConnectError("Restore failed: no bridge_url found in storage.")

        self.wallet_app = WalletApp.from_dict(connection.get("wallet_app") or {})
        self.session.bridge_url = self.wallet_app.bridge_url
        self._api_token = self._choose_api_token(self.api_tokens, self.wallet_app)

        connect_event = connection.get("connect_event")
        payload = connect_event.get("payload") if connect_event else None
        if payload is None:
            raise TonConnectError("Failed to restore connection: no payload found in stored response.")

        await self.start_sse()
        return WalletInfo.from_payload(payload)

    async def close_connection(self) -> None:
        """
        Stops the SSE subscription and clears the current session data.
        """
        if not self.client_session_closed:
            await self.pause_sse()

        self.session = BridgeSession()
        self.pending_requests.clear()

    async def update_session(self, event: Dict[str, Any], wallet_public_key: str) -> None:
        """
        Updates session data on CONNECT events and persists it to storage,
        enabling future reconnection.

        :param event: A dictionary with event data.
        :param wallet_public_key: The wallet's public key.
        """
        logger.debug(f"Updating session for wallet public key: {wallet_public_key}.")
        self.session.wallet_public_key = wallet_public_key

        connection = {
            "type": "http",
            "session": self.session.get_dict(),
            "last_wallet_event_id": event.get("id"),
            "connect_event": event,
            "next_rpc_request_id": 0,
            "wallet_app": self.wallet_app.to_dict() if self.wallet_app else {},
        }

        await self.storage.set_item(self.storage.KEY_CONNECTION, json.dumps(connection))

    async def remove_session(self) -> None:
        """
        Removes session data from storage and closes the current connection.
        """
        await self.close()
        await self.storage.remove_item(self.storage.KEY_CONNECTION)
        await self.storage.remove_item(self.storage.KEY_LAST_EVENT_ID)

    async def close(self) -> None:
        """
        Completely closes the HTTPBridge, including the subscription and session cleanup.
        """
        self._is_closed = True
        await self.close_connection()
