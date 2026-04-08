from dataclasses import dataclass


@dataclass
class ServerInfo:
    """Server identity for status display."""

    index: int
    """Positional index in the config."""

    host: str
    """IP address string."""

    port: int
    """Port number."""
