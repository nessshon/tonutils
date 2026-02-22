import time
import typing as t

from tonutils.tonconnect.models._types import A, BaseModel
from tonutils.tonconnect.models.request import ConnectRequest
from tonutils.tonconnect.models.response import ConnectEventSuccess
from tonutils.tonconnect.models.session import BridgeProviderSession, SessionKeyPair


class ConnectionSource(BaseModel):
    """Bridge endpoint with universal link.

    Attributes:
        bridge_url: Bridge base URL.
        universal_link: Wallet universal link.
    """

    bridge_url: str = A("bridgeUrl")
    universal_link: str = A("universalLink")


ConnectionSources = t.List[ConnectionSource]


class PendingConnection(BaseModel):
    """Pending (not yet accepted) TonConnect connection.

    Attributes:
        connect_request: Original connect request.
        connection_sources: Available bridge endpoints.
        session_keypair: Session X25519 key pair.
        created_at: Creation unix timestamp, or `None`.
    """

    connect_request: ConnectRequest = A("connectRequest")
    connection_sources: ConnectionSources = A("connectionSources")
    session_keypair: SessionKeyPair = A("sessionKeyPair")
    created_at: t.Optional[int] = A("createdAt", default=None)

    def is_expired(self) -> bool:
        """Check whether the pending connection has expired (15 min TTL)."""
        if self.created_at is not None:
            now = int(time.time())
            return (now - self.created_at) > 15 * 60
        return True


class ActiveConnection(BaseModel):
    """Established TonConnect connection.

    Attributes:
        type: Connection type.
        connect_event: Successful connect event.
        session: Bridge provider session.
        last_event_id: Last SSE event ID, or `None`.
        next_rpc_request_id: Next RPC request sequence number.
        last_wallet_event_id: Last wallet event ID, or `None`.
    """

    type: t.Literal["http"] = "http"
    connect_event: ConnectEventSuccess = A("connectEvent")
    session: BridgeProviderSession
    next_rpc_request_id: int = A("nextRpcRequestId", default=0)
    last_wallet_event_id: t.Optional[int] = A("lastWalletEventId", default=None)
    last_event_id: t.Optional[str] = A("lastEventId", default=None)


Connection: t.TypeAlias = t.Union[
    ActiveConnection,
    PendingConnection,
]
