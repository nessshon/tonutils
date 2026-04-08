from typing import ClassVar

from tonutils.tools.status_monitor.console import Console
from tonutils.tools.status_monitor.lite.models import BlockInfo, LiteServerStatus

__all__ = ["LiteConsole"]


class LiteConsole(Console):
    """Terminal renderer for liteserver status table."""

    HEADERS: ClassVar[list[str]] = [
        "#",
        "HOST",
        "PORT",
        "Version",
        "Time",
        "Ping",
        "Connect RTT",
        "Request RTT",
        "Last MC Block",
        "Last BC Block",
        "Archive From",
    ]
    """Column headers for the liteserver status table."""

    WIDTHS: ClassVar[list[int]] = [2, 15, 5, 7, 19, 7, 11, 11, 16, 16, 12]
    """Column widths in characters."""

    TABLE_TITLE = "Lite Server Status"
    """Title displayed above the table."""

    ERROR_PREFIX = "LS"
    """Short label used in error log entries."""

    def _format_row(self, status: LiteServerStatus) -> str:
        """Format a single status row."""
        cells = [
            str(status.server.index),
            status.server.host,
            str(status.server.port),
            self._fmt_int(status.version),
            self._fmt_datetime(status.time),
            self._fmt_ms(status.ping_ms),
            self._fmt_ms(status.connect_ms),
            self._fmt_ms(status.request_ms),
            self._fmt_block(status.last_mc_block),
            self._fmt_block(status.last_bc_block),
            self._fmt_date(status.archive_from),
        ]
        return " \u2502 ".join(c.ljust(w) for c, w in zip(cells, self.WIDTHS, strict=True))

    @staticmethod
    def _fmt_block(block: BlockInfo | None) -> str:
        """Format block as ``seqno / txs_count``, ``-`` if ``None``."""
        if block is None:
            return "-"
        return f"{block.seqno} / {block.txs_count}"
