from dataclasses import dataclass

from tonutils.utils.status_monitor.models import ServerInfo

__all__ = ["BlockInfo", "LiteServerStatus"]


@dataclass
class BlockInfo:
    """Block summary for status display."""

    seqno: int
    """Block sequence number."""

    txs_count: int
    """Number of transactions in the block."""


@dataclass
class LiteServerStatus:
    """Snapshot of a single liteserver's health."""

    server: ServerInfo
    """Liteserver identity."""

    version: int | None = None
    """Server software version, or ``None``."""

    time: int | None = None
    """Server unix timestamp, or ``None``."""

    ping_ms: int | None = None
    """Last ping latency in ms, or ``None``."""

    connect_ms: int | None = None
    """Connection RTT in ms, or ``None``."""

    request_ms: int | None = None
    """Request RTT in ms, or ``None``."""

    last_mc_block: BlockInfo | None = None
    """Latest masterchain block info, or ``None``."""

    last_bc_block: BlockInfo | None = None
    """Latest basechain block info, or ``None``."""

    archive_from: int | None = None
    """Earliest archive unix timestamp, or ``None``."""

    last_error: str | None = None
    """Most recent error message, or ``None``."""
