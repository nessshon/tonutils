from dataclasses import dataclass

from tonutils.utils.status_monitor.models import ServerInfo

__all__ = ["DhtNodeStatus"]


@dataclass
class DhtNodeStatus:
    """Snapshot of a single DHT node's health."""

    server: ServerInfo
    """DHT node identity."""

    adnl_id: str = ""
    """Full ADNL key ID in uppercase hex."""

    version: int | None = None
    """Address list version, or ``None``."""

    ping_ms: int | None = None
    """Last ping latency in ms, or ``None``."""

    connect_ms: int | None = None
    """Channel establishment RTT in ms, or ``None``."""

    request_ms: int | None = None
    """``dht.findNode`` RTT in ms, or ``None``."""

    neighbors: str | None = None
    """Neighbor count string (e.g. ``"5/7"``), or ``None``."""

    last_error: str | None = None
    """Most recent error message, or ``None``."""
