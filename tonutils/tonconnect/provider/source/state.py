from enum import Enum


class ReadyState(int, Enum):
    """SSE connection state.

    Attributes:
        CONNECTING: Connection in progress (0).
        OPEN: Connected and receiving events (1).
        CLOSED: Connection closed (2).
    """

    CONNECTING = 0
    OPEN = 1
    CLOSED = 2
