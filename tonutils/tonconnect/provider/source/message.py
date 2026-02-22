from __future__ import annotations

import typing as t
from dataclasses import dataclass


@dataclass(slots=True)
class EventMessage:
    """Parsed SSE event message.

    Attributes:
        event: Event type name.
        data: Event payload, or `None`.
        event_id: Event identifier, or `None`.
    """

    event: str = "message"
    data: t.Optional[str] = None
    event_id: t.Optional[str] = None

    @classmethod
    def parse(cls, raw: str) -> EventMessage:
        """Parse a raw SSE event block into an `EventMessage`.

        :param raw: Raw SSE text block (lines separated by newlines).
        :return: Parsed event message.
        """
        event: str = "message"
        data_parts: t.List[str] = []
        event_id: t.Optional[str] = None

        for line in raw.splitlines():
            if not line or line.startswith(":"):
                continue

            field, sep, value = line.partition(":")
            if not sep:
                continue

            if value.startswith(" "):
                value = value[1:]

            if field == "data":
                data_parts.append(value)
            elif field == "event":
                event = value or "message"
            elif field == "id":
                event_id = value or None

        data = "\n".join(data_parts) if data_parts else None
        return cls(event=event, data=data, event_id=event_id)
