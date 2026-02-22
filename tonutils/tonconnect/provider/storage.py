import asyncio
import time
import typing as t

from pydantic import ValidationError, TypeAdapter

from tonutils.tonconnect.exceptions import TonConnectError
from tonutils.tonconnect.models.connection import (
    Connection,
    ActiveConnection,
    PendingConnection,
)
from tonutils.tonconnect.storage import StorageProtocol


class ProviderStorage:
    """High-level storage wrapper for TonConnect provider state."""

    _key_prefix = "ton-connect-storage"
    _connection_adapter = TypeAdapter(Connection)

    def __init__(self, storage: StorageProtocol, session_key: str) -> None:
        """
        :param storage: Underlying key-value storage.
        :param session_key: Unique session identifier for key namespacing.
        """
        self._storage = storage
        self._lock = asyncio.Lock()
        self._key = f"{self._key_prefix}::{session_key}"

    async def _get_connection(self) -> t.Optional[Connection]:
        """Load and validate connection from storage, or `None`."""
        raw = await self._storage.get_item(self._key)
        if not isinstance(raw, dict):
            return None

        try:
            conn = self._connection_adapter.validate_python(raw)
        except ValidationError:
            await self.remove_connection()
            return None

        if isinstance(conn, PendingConnection) and conn.is_expired():
            await self.remove_connection()
            return None

        return conn

    async def store_connection(self, connection: Connection) -> None:
        """Persist a connection (pending or active).

        :param connection: Connection to store.
        """
        if isinstance(connection, PendingConnection) and connection.created_at is None:
            connection = connection.model_copy(update={"created_at": int(time.time())})

        conn = connection.dump()
        await self._storage.set_item(self._key, conn)

    async def remove_connection(self) -> None:
        """Remove the stored connection."""
        await self._storage.remove_item(self._key)

    async def get_connection(self) -> Connection:
        """Load the stored connection.

        :return: Active or pending connection.
        :raises TonConnectError: If no connection is stored.
        """
        conn = await self._get_connection()
        if not conn:
            raise TonConnectError(
                "Trying to read connection source while nothing is stored"
            )

        return conn

    async def get_pending_connection(self) -> PendingConnection:
        """Load the stored pending connection.

        :return: Pending connection.
        :raises TonConnectError: If no pending connection is stored.
        """
        conn = await self._get_connection()
        if not conn:
            raise TonConnectError(
                "Trying to read connection source while nothing is stored"
            )

        if not isinstance(conn, PendingConnection):
            raise TonConnectError(
                "Trying to read inflight connection while connection is stored"
            )

        return conn

    async def store_last_wallet_event_id(self, event_id: int) -> None:
        """Persist the last wallet event ID.

        :param event_id: Monotonic event identifier.
        """
        async with self._lock:
            conn = await self._get_connection()
            if isinstance(conn, ActiveConnection):
                conn = conn.model_copy(update={"last_wallet_event_id": int(event_id)})
                await self.store_connection(conn)

    async def get_last_wallet_event_id(self) -> t.Optional[int]:
        """Return the last wallet event ID, or `None`."""
        conn = await self._get_connection()
        if isinstance(conn, ActiveConnection):
            return conn.last_wallet_event_id
        return None

    async def increase_next_rpc_request_id(self) -> None:
        """Increment the next RPC request ID in storage."""
        async with self._lock:
            conn = await self._get_connection()
            if isinstance(conn, ActiveConnection):
                last_id = int(conn.next_rpc_request_id or 0)
                conn = conn.model_copy(update={"next_rpc_request_id": last_id + 1})
                await self.store_connection(conn)

    async def get_next_rpc_request_id(self) -> int:
        """Return the next RPC request ID (0 if not active)."""
        conn = await self._get_connection()
        if isinstance(conn, ActiveConnection):
            return int(conn.next_rpc_request_id or 0)
        return 0

    async def store_last_event_id(self, last_event_id: str) -> None:
        """Persist the last SSE event ID.

        :param last_event_id: SSE event identifier string.
        """
        async with self._lock:
            conn = await self._get_connection()
            if isinstance(conn, ActiveConnection):
                conn = conn.model_copy(update={"last_event_id": last_event_id})
                await self.store_connection(conn)

    async def get_last_event_id(self) -> t.Optional[str]:
        """Return the last SSE event ID, or `None`."""
        conn = await self._get_connection()
        if isinstance(conn, ActiveConnection):
            return conn.last_event_id
        return None
