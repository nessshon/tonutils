from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Union


class Event(str, Enum):
    """
    Represents the standard events in the TonConnect lifecycle.
    """
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    TRANSACTION = "transaction"


class EventError(str, Enum):
    """
    Represents error events corresponding to standard TonConnect events.
    """
    CONNECT = "connect_error"
    DISCONNECT = "disconnect_error"
    TRANSACTION = "transaction_error"


# Type alias for event handler functions.
# An EventHandler is an asynchronous callable that takes any arguments and returns None.
EventHandler = Callable[..., Awaitable[None]]

# Dictionary mapping events (both standard and error events) to lists of handlers.
EventHandlers = Dict[Union[Event, EventError], List[EventHandler]]

# Dictionary mapping events to their associated data.
EventHandlersData = Dict[Union[Event, EventError], Dict[str, Any]]
