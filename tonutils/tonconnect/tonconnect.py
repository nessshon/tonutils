import asyncio
from copy import copy
from typing import Optional, List, Dict, Callable, Union

from tonutils.tonconnect.utils.exceptions import TonConnectError
from tonutils.tonconnect.utils.logger import logger
from tonutils.tonconnect.utils.wallet_manager import WalletsListManager
from .connector import Connector
from .models import WalletApp
from .models.event import (
    Event,
    EventError,
    EventHandler,
    EventHandlers,
    EventHandlersData,
)
from .storage import IStorage


class TonConnect:
    """
    Manages multiple user sessions, each represented by a Connector.
    Provides event handling, connection restoration, and wallet list retrieval.
    """

    def __init__(
            self,
            storage: IStorage,
            manifest_url: str,
            api_tokens: Optional[Dict[str, str]] = None,
            exclude_wallets: Optional[List[str]] = None,
            include_wallets: Optional[List[str]] = None,
            wallets_list_cache_ttl: Optional[int] = None,
            wallets_list_source_url: Optional[str] = None,
    ) -> None:
        """
        Initializes the TonConnect class with storage, manifest URL, and wallet list options.

        :param storage: The main storage interface shared by all users.
        :param manifest_url: The DApp's manifest URL to be used by each Connector.
        :param api_tokens: Optional dictionary mapping API names to tokens for authorization.
        :param exclude_wallets: Optional list of wallet IDs or names to exclude from the wallet list.
        :param include_wallets: Optional list of wallet IDs or names to include.
        :param wallets_list_cache_ttl: Optional cache TTL for the wallet list.
        :param wallets_list_source_url: Optional source URL for the wallet list.
        """
        self.storage = storage
        self.manifest_url = manifest_url
        self.api_tokens = api_tokens

        self._wallets_list_manager = WalletsListManager(
            source_url=wallets_list_source_url,
            include_wallets=include_wallets,
            exclude_wallets=exclude_wallets,
            cache_ttl=wallets_list_cache_ttl,
        )

        self._event_handlers = self._initialize_event_handlers()
        self._events_data = self._initialize_events_data()

        self._connectors: Dict[int, Connector] = {}
        self._connectors_lock = asyncio.Lock()
        logger.debug(f"TonConnect initialized with manifest URL: {self.manifest_url}")

    @staticmethod
    def _initialize_event_handlers() -> EventHandlers:
        """
        Creates a default mapping of events to empty handler lists.

        :return: A dictionary keyed by event, each value an empty list of handlers.
        """
        return {
            Event.CONNECT: [],
            EventError.CONNECT: [],
            Event.DISCONNECT: [],
            EventError.DISCONNECT: [],
            Event.TRANSACTION: [],
            EventError.TRANSACTION: [],
        }

    @staticmethod
    def _initialize_events_data() -> EventHandlersData:
        """
        Creates a default mapping of events to empty data dictionaries.

        :return: A dictionary keyed by event, each value an empty dict for storing event-specific data.
        """
        return {
            Event.CONNECT: {},
            EventError.CONNECT: {},
            Event.DISCONNECT: {},
            EventError.DISCONNECT: {},
            Event.TRANSACTION: {},
            EventError.TRANSACTION: {},
        }

    def _init_user_storage(self, user_id: int) -> IStorage:
        """
        Creates a user-specific storage instance by copying the main storage
        and altering key prefixes to isolate data for each user.

        :param user_id: The user identifier.
        :return: A modified copy of the original storage for this user.
        """
        user_storage = copy(self.storage)
        user_storage.KEY_CONNECTION = f"{user_id}:{user_storage.KEY_CONNECTION}"
        user_storage.KEY_LAST_EVENT_ID = f"{user_id}:{user_storage.KEY_LAST_EVENT_ID}"
        return user_storage

    def register_event(self, event: Union[Event, EventError], handler: EventHandler) -> None:
        """
        Registers a handler for a specific event.

        :param event: The event (or error event) to handle.
        :param handler: The function or coroutine that handles this event.
        """
        logger.debug(f"Registering handler for event: {event.name}")
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def on_event(self, event: Union[Event, EventError]) -> Callable[[EventHandler], EventHandler]:
        """
        Decorator for registering event handlers more conveniently.

        :param event: The event (or error event) to handle.
        :return: A decorator that accepts the handler function.
        """

        def decorator(handler: EventHandler) -> EventHandler:
            self.register_event(event, handler)
            logger.debug(f"Handler {handler.__name__} registered for event: {event.name}")
            return handler

        return decorator

    async def create_connector(self, user_id: int) -> Connector:
        """
        Creates a new Connector for the given user, along with a user-specific storage object.

        :param user_id: The user identifier.
        :return: The newly created Connector instance.
        """
        user_storage = self._init_user_storage(user_id)
        connector = Connector(
            user_id=user_id,
            manifest_url=self.manifest_url,
            storage=user_storage,
            on_events=self._event_handlers,
            on_events_data=self._events_data,
            api_tokens=self.api_tokens or {},
        )
        self._connectors[user_id] = connector

        logger.debug(f"Connector created for user_id={user_id}")
        return connector

    async def get_connector(self, user_id: int) -> Optional[Connector]:
        """
        Retrieves the Connector instance for the specified user.

        :param user_id: The user identifier.
        :return: The Connector instance, or None if not found.
        """
        async with self._connectors_lock:
            return self._connectors.get(user_id)

    async def init_connector(self, user_id: int) -> Connector:
        """
        Retrieves or creates a Connector for the specified user, then attempts to restore any existing connection.

        :param user_id: The user identifier.
        :return: The ready-to-use Connector instance.
        """
        async with self._connectors_lock:
            if user_id in self._connectors:
                connector = self._connectors[user_id]
            else:
                connector = await self.create_connector(user_id)

            # If there's no active wallet or the connector’s bridge session is closed, try to restore it.
            if connector.wallet is None or connector.bridge.client_session_closed:
                try:
                    await connector.restore_connection()
                    logger.debug(f"Connection restored for user_id={user_id}")
                except TonConnectError:
                    logger.debug(f"Failed to restore connection for user_id={user_id}")
                    pass

            return connector

    async def get_wallets(self) -> List[WalletApp]:
        """
        Retrieves a list of wallets from the configured WalletsListManager.

        :return: A list of WalletApp objects.
        """
        return await self._wallets_list_manager.get_wallets()

    async def run_all(self, user_ids: List[int]) -> None:
        """
        Initializes connectors for all specified user IDs.

        :param user_ids: A list of user identifiers.
        """
        logger.debug(f"Initializing connectors for user_ids={user_ids}")
        async with self._connectors_lock:
            for user_id in user_ids:
                await self.create_connector(user_id)

    async def close_all(self) -> None:
        """
        Closes (pauses) all connectors by stopping SSE subscriptions.

        This does not remove the sessions; it only pauses them.
        """
        logger.debug("Closing all active connectors")
        async with self._connectors_lock:
            pause_tasks = [connector.pause() for connector in self._connectors.values()]
        await asyncio.gather(*pause_tasks)
