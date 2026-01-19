import sys
import typing as t
from collections import deque
from datetime import datetime

from tonutils.tools.status_monitor.models import BlockInfo, LiteServerStatus

_ENTER_ALT_SCREEN = "\033[?1049h"
_EXIT_ALT_SCREEN = "\033[?1049l"
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"
_MOVE_HOME = "\033[H"
_CLEAR_SCREEN = "\033[2J"
_CLEAR_LINE = "\033[K"


class Console:
    HEADERS = [
        "LS",
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
    WIDTHS = [2, 15, 5, 7, 19, 7, 11, 11, 16, 16, 12]

    TABLE_TITLE = "Lite Server Status"
    ERROR_TITLE = "Error Log"
    MAX_ERROR_LOGS = 10

    def __init__(self) -> None:
        self._index_width = 2
        self._is_tty = sys.stdout.isatty()
        self._error_log: deque[str] = deque(maxlen=self.MAX_ERROR_LOGS)
        self._prev_errors: t.Dict[int, t.Optional[str]] = {}

    def enter(self) -> None:
        if self._is_tty:
            sys.stdout.write(_ENTER_ALT_SCREEN + _HIDE_CURSOR + _CLEAR_SCREEN)
            sys.stdout.flush()

    def exit(self) -> None:
        if self._is_tty:
            sys.stdout.write(_SHOW_CURSOR + _EXIT_ALT_SCREEN)
            sys.stdout.flush()

    def render(self, statuses: t.List[LiteServerStatus]) -> None:
        self._update_state(statuses)
        self._home()
        self._draw(statuses)

    def _home(self) -> None:
        if self._is_tty:
            sys.stdout.write(_MOVE_HOME)
            sys.stdout.flush()

    def _update_state(self, statuses: t.List[LiteServerStatus]) -> None:
        self._update_index_width(statuses)
        self._update_error_log(statuses)

    def _update_index_width(self, statuses: t.List[LiteServerStatus]) -> None:
        if statuses:
            self._index_width = max(2, len(str(len(statuses) - 1)))

    def _update_error_log(self, statuses: t.List[LiteServerStatus]) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for status in statuses:
            prev = self._prev_errors.get(status.server.index)
            if status.last_error and status.last_error != prev:
                idx = str(status.server.index).rjust(self._index_width)
                self._error_log.appendleft(f"  {now} [LS {idx}]: {status.last_error}")
            self._prev_errors[status.server.index] = status.last_error

    def _get_table_width(self) -> int:
        return sum(self.WIDTHS) + (len(self.WIDTHS) - 1) * 3

    def _draw(self, statuses: t.List[LiteServerStatus]) -> None:
        table_width = self._get_table_width()
        padding = (table_width - len(self.TABLE_TITLE)) // 2

        lines = [
            "═" * table_width,
            " " * padding + self.TABLE_TITLE,
            "═" * table_width,
            self._format_header(),
            self._format_separator(),
        ]

        for status in statuses:
            lines.append(self._format_row(status))

        lines.append("")

        if self._error_log:
            lines.append("─" * table_width)
            lines.append(f"  {self.ERROR_TITLE}:")
            lines.extend(self._error_log)

        output = (_CLEAR_LINE + "\n").join(lines) + _CLEAR_LINE

        output += "\n" + _CLEAR_LINE
        sys.stdout.write(output)
        sys.stdout.flush()

    def _format_header(self) -> str:
        return " │ ".join(h.ljust(w) for h, w in zip(self.HEADERS, self.WIDTHS))

    def _format_separator(self) -> str:
        return "─┼─".join("─" * w for w in self.WIDTHS)

    def _format_row(self, status: LiteServerStatus) -> str:
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
        return " │ ".join(c.ljust(w) for c, w in zip(cells, self.WIDTHS))

    @staticmethod
    def _fmt_int(value: t.Optional[int]) -> str:
        return str(value) if value is not None else "-"

    @staticmethod
    def _fmt_ms(value: t.Optional[int]) -> str:
        return f"{value}ms" if value is not None else "-"

    @staticmethod
    def _fmt_block(block: t.Optional[BlockInfo]) -> str:
        if block is None:
            return "-"
        return f"{block.seqno} / {block.txs_count}"

    @staticmethod
    def _fmt_date(ts: t.Optional[int]) -> str:
        if ts is None:
            return "-"
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

    @staticmethod
    def _fmt_datetime(ts: t.Optional[int]) -> str:
        if ts is None:
            return "-"
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
