import sys
import typing as t
from collections import deque
from datetime import datetime
from typing import ClassVar

__all__ = ["Console"]

_ENTER_ALT_SCREEN = "\033[?1049h"
_EXIT_ALT_SCREEN = "\033[?1049l"
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"
_MOVE_HOME = "\033[H"
_CLEAR_SCREEN = "\033[2J"
_CLEAR_LINE = "\033[K"


class Console:
    """Base terminal renderer for node status tables."""

    HEADERS: ClassVar[list[str]]
    """Column headers for the status table."""

    WIDTHS: ClassVar[list[int]]
    """Column widths in characters."""

    TABLE_TITLE: ClassVar[str]
    """Title displayed above the table."""

    ERROR_PREFIX: ClassVar[str]
    """Short label used in error log entries."""

    MAX_ERROR_LOGS: ClassVar[int] = 10
    """Maximum number of recent errors shown in the error log."""

    ERROR_TITLE = "Error Log"
    """Heading for the error log section."""

    def __init__(self) -> None:
        """Initialize console state and error tracking."""
        self._index_width = 2
        self._is_tty = sys.stdout.isatty()
        self._error_log: deque[str] = deque(maxlen=self.MAX_ERROR_LOGS)
        self._prev_errors: dict[int, str | None] = {}

    def enter(self) -> None:
        """Switch to alternate screen and hide cursor."""
        if self._is_tty:
            sys.stdout.write(_ENTER_ALT_SCREEN + _HIDE_CURSOR + _CLEAR_SCREEN)
            sys.stdout.flush()

    def exit(self) -> None:
        """Restore main screen and show cursor."""
        if self._is_tty:
            sys.stdout.write(_SHOW_CURSOR + _EXIT_ALT_SCREEN)
            sys.stdout.flush()

    def render(self, statuses: list[t.Any]) -> None:
        """Redraw the full status table.

        :param statuses: Current node statuses.
        """
        self._update_state(statuses)
        self._home()
        self._draw(statuses)

    def _home(self) -> None:
        """Move cursor to top-left."""
        if self._is_tty:
            sys.stdout.write(_MOVE_HOME)
            sys.stdout.flush()

    def _update_state(self, statuses: list[t.Any]) -> None:
        """Update index width and error log from statuses."""
        self._update_index_width(statuses)
        self._update_error_log(statuses)

    def _update_index_width(self, statuses: list[t.Any]) -> None:
        """Recalculate index column width."""
        if statuses:
            self._index_width = max(2, len(str(len(statuses) - 1)))

    def _update_error_log(self, statuses: list[t.Any]) -> None:
        """Append new errors to the rolling error log."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for status in statuses:
            prev = self._prev_errors.get(status.server.index)
            if status.last_error and status.last_error != prev:
                idx = str(status.server.index).rjust(self._index_width)
                self._error_log.appendleft(f"  {now} [{self.ERROR_PREFIX} {idx}]: {status.last_error}")
            self._prev_errors[status.server.index] = status.last_error

    def _get_table_width(self) -> int:
        """Return total table width in characters."""
        return sum(self.WIDTHS) + (len(self.WIDTHS) - 1) * 3

    def _draw(self, statuses: list[t.Any]) -> None:
        """Write the full table and error log to stdout."""
        table_width = self._get_table_width()
        padding = (table_width - len(self.TABLE_TITLE)) // 2

        lines = [
            "\u2550" * table_width,
            " " * padding + self.TABLE_TITLE,
            "\u2550" * table_width,
            self._format_header(),
            self._format_separator(),
        ]

        lines.extend(self._format_row(status) for status in statuses)

        lines.append("")

        if self._error_log:
            lines.append("\u2500" * table_width)
            lines.append(f"  {self.ERROR_TITLE}:")
            lines.extend(self._error_log)

        output = (_CLEAR_LINE + "\n").join(lines) + _CLEAR_LINE
        output += "\n" + _CLEAR_LINE
        sys.stdout.write(output)
        sys.stdout.flush()

    def _format_header(self) -> str:
        """Format the column header row."""
        return " \u2502 ".join(h.ljust(w) for h, w in zip(self.HEADERS, self.WIDTHS, strict=True))

    def _format_separator(self) -> str:
        """Format the header/body separator row."""
        return "\u2500\u253c\u2500".join("\u2500" * w for w in self.WIDTHS)

    def _format_row(self, status: t.Any) -> str:
        """Format a single status row."""
        raise NotImplementedError

    @staticmethod
    def _fmt_ms(value: int | None) -> str:
        """Format optional millisecond value, ``-`` if ``None``."""
        return f"{value}ms" if value is not None else "-"

    @staticmethod
    def _fmt_int(value: int | None) -> str:
        """Format optional integer, ``-`` if ``None``."""
        return str(value) if value is not None else "-"

    @staticmethod
    def _fmt_date(ts: int | None) -> str:
        """Format unix timestamp as date, ``-`` if ``None``."""
        if ts is None:
            return "-"
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

    @staticmethod
    def _fmt_datetime(ts: int | None) -> str:
        """Format unix timestamp as datetime, ``-`` if ``None``."""
        if ts is None:
            return "-"
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
