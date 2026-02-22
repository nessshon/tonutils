import typing as t
from codecs import getincrementaldecoder

from tonutils.tonconnect.provider.source.message import EventMessage

_UTF8_DECODER = getincrementaldecoder("utf-8")


class EventDecoder:
    """Incremental SSE stream decoder."""

    def __init__(self) -> None:
        self._decoder = _UTF8_DECODER()
        self._buffer: str = ""

    def reset(self) -> None:
        """Reset decoder and buffer state."""
        self._decoder = _UTF8_DECODER()
        self._buffer = ""

    def feed(self, chunk: bytes) -> t.List[EventMessage]:
        """Decode a chunk and return any complete events.

        :param chunk: Raw bytes from the SSE stream.
        :return: List of parsed events (maybe empty).
        """
        text = self._decoder.decode(chunk)
        if not text:
            return []

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        self._buffer += text

        buf = self._buffer
        events: t.List[EventMessage] = []

        while True:
            sep = buf.find("\n\n")
            if sep == -1:
                break

            raw_event = buf[:sep]
            buf = buf[sep + 2 :]

            if raw_event.strip():
                events.append(EventMessage.parse(raw_event))

        self._buffer = buf
        return events

    def flush(self) -> t.List[EventMessage]:
        """Flush remaining buffer and return any trailing event.

        :return: List with at most one event.
        """
        raw = self._buffer
        self.reset()

        if raw.strip():
            return [EventMessage.parse(raw)]
        return []
