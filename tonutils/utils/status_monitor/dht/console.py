from typing import ClassVar

from tonutils.utils.status_monitor.console import Console
from tonutils.utils.status_monitor.dht.models import DhtNodeStatus

__all__ = ["DhtConsole"]


class DhtConsole(Console):
    """Terminal renderer for DHT node status table."""

    HEADERS: ClassVar[list[str]] = [
        "#",
        "HOST",
        "PORT",
        "ADNL",
        "Version",
        "Ping",
        "Connect RTT",
        "Request RTT",
        "Peers",
    ]
    """Column headers for the DHT status table."""

    WIDTHS: ClassVar[list[int]] = [2, 15, 5, 64, 10, 7, 11, 11, 9]
    """Column widths in characters."""

    TABLE_TITLE = "DHT Node Status"
    """Title displayed above the table."""

    ERROR_PREFIX = "DHT"
    """Short label used in error log entries."""

    def _format_row(self, status: DhtNodeStatus) -> str:
        """Format a single status row."""
        cells = [
            str(status.server.index),
            status.server.host,
            str(status.server.port),
            status.adnl_id if status.adnl_id else "-",
            str(status.version) if status.version is not None else "-",
            self._fmt_ms(status.ping_ms),
            self._fmt_ms(status.connect_ms),
            self._fmt_ms(status.request_ms),
            status.neighbors if status.neighbors is not None else "-",
        ]
        return " \u2502 ".join(c.ljust(w) for c, w in zip(cells, self.WIDTHS, strict=True))
