from __future__ import annotations

import time
import typing as t

from tonutils.exceptions import ProviderResponseError
from tonutils.transports.worker import BaseWorker

if t.TYPE_CHECKING:
    from tonutils.providers.dht.provider import DhtProvider


class DhtReaderWorker(BaseWorker):
    """Background reader for ADNL-UDP datagrams.

    Receives raw packets from the transport, decrypts them,
    deserializes ``adnl.packetContents``, extracts inner messages,
    handles ``adnl.message.part`` reassembly, and dispatches:

    - ``confirmChannel`` → transport (channel pending futures)
    - ``answer`` → provider (query pending futures)
    """

    def __init__(self, provider: DhtProvider) -> None:
        """Initialize the reader worker.

        :param provider: Parent DHT provider.
        """
        super().__init__(provider)
        self._parts: dict[str, dict[int, bytes]] = {}
        self._part_totals: dict[str, int] = {}
        self._part_timestamps: dict[str, float] = {}
        self._part_ttl: float = 10.0

    @staticmethod
    def _update_peer_state(peer_state: t.Any, packet: dict[str, t.Any]) -> None:
        """Update peer seqno and reinit date from incoming packet.

        :param peer_state: ``_PeerState`` instance.
        :param packet: Deserialized ``adnl.packetContents``.
        """
        reinit_date = packet.get("reinit_date", 0)
        if isinstance(reinit_date, int) and reinit_date > 0 and reinit_date > peer_state.dst_reinit_date:
            peer_state.dst_reinit_date = reinit_date
            peer_state.confirm_seqno = 0

        seqno = packet.get("seqno", 0)
        if isinstance(seqno, int) and seqno > peer_state.confirm_seqno:
            peer_state.confirm_seqno = seqno

    def _resolve_future(self, key: str, result: t.Any) -> None:
        """Pop a pending future by key and set its result.

        :param key: Future lookup key (hex string).
        :param result: Value to set on the future.
        """
        fut = self.provider.pending.pop(key, None)
        if fut is None or fut.done():
            return

        if isinstance(result, dict) and "code" in result and "message" in result:
            fut.set_exception(
                ProviderResponseError(
                    code=result["code"],
                    message=result["message"],
                    endpoint="dht",
                )
            )
        else:
            fut.set_result(result)

    def _cleanup_stale_parts(self) -> None:
        """Remove incomplete fragment sets that have exceeded TTL."""
        now = time.monotonic()
        stale = [k for k, ts in self._part_timestamps.items() if now - ts > self._part_ttl]
        for k in stale:
            self._parts.pop(k, None)
            self._part_totals.pop(k, None)
            self._part_timestamps.pop(k, None)

    def _handle_part(self, msg: dict[str, t.Any]) -> bytes | None:
        """Accumulate ``adnl.message.part`` fragments.

        :param msg: Deserialized part message.
        :return: Reassembled payload when all parts received, or ``None``.
        """
        self._cleanup_stale_parts()

        msg_hash = msg.get("hash", b"")
        if isinstance(msg_hash, bytes):
            msg_hash = msg_hash.hex()
        offset = msg.get("offset", 0)
        total = msg.get("total_size", 0)
        data = msg.get("data", b"")

        if not msg_hash:
            return None

        if msg_hash not in self._parts:
            self._parts[msg_hash] = {}
            self._part_totals[msg_hash] = total
            self._part_timestamps[msg_hash] = time.monotonic()

        self._parts[msg_hash][offset] = data

        collected = sum(len(v) for v in self._parts[msg_hash].values())
        if collected >= self._part_totals[msg_hash]:
            offsets = sorted(self._parts[msg_hash].keys())
            reassembled = b"".join(self._parts[msg_hash][o] for o in offsets)
            del self._parts[msg_hash]
            del self._part_totals[msg_hash]
            del self._part_timestamps[msg_hash]
            return reassembled

        return None

    @staticmethod
    def _extract_messages(packet: dict[str, t.Any]) -> list[dict[str, t.Any]]:
        """Extract inner messages from ``adnl.packetContents``.

        :param packet: Deserialized packet contents.
        :return: List of inner message dicts.
        """
        messages: list[dict[str, t.Any]] = []

        single = packet.get("message")
        if isinstance(single, dict):
            messages.append(single)

        multi = packet.get("messages")
        if isinstance(multi, list):
            messages.extend(m for m in multi if isinstance(m, dict))

        return messages

    def _dispatch_message(self, msg: dict[str, t.Any]) -> None:
        """Dispatch a single deserialized ADNL message.

        - ``confirmChannel`` → transport channel pending
        - ``answer`` → provider query pending
        - ``part`` → fragment reassembly

        :param msg: Deserialized ADNL message dict.
        """
        tl_type = msg.get("@type", "")

        if tl_type == "adnl.message.confirmChannel":
            peer_key = msg.get("peer_key", "")
            if isinstance(peer_key, bytes):
                peer_key = peer_key.hex()
            if not self.provider.transport.resolve_channel_confirm(peer_key, msg):
                self._resolve_future(peer_key, msg)

        elif tl_type == "adnl.message.answer":
            query_id = msg.get("query_id", "")
            if isinstance(query_id, bytes):
                query_id = query_id.hex()
            answer = msg.get("answer", b"")

            if isinstance(answer, dict):
                self._resolve_future(query_id, answer)
                return

            try:
                inner = self.provider.codec.deserialize(answer)
            except Exception:
                return

            if inner:
                self._resolve_future(query_id, inner[0])

        elif tl_type == "adnl.message.part":
            reassembled = self._handle_part(msg)
            if reassembled is not None:
                try:
                    inner = self.provider.codec.deserialize(reassembled)
                except Exception:
                    return
                if inner:
                    self._dispatch_message(inner[0])

    async def _run(self) -> None:
        """Continuously read UDP datagrams, decrypt, and dispatch."""
        transport = self.provider.transport
        codec = self.provider.codec

        while self.running:
            try:
                raw, addr = await transport.recv_raw()
            except Exception:
                continue

            if len(raw) < 64:
                continue

            plaintext, peer_state = transport.decrypt_incoming(raw)
            if not plaintext:
                continue

            if peer_state is None:
                endpoint = f"{addr[0]}:{addr[1]}"
                peer_state = transport.get_peer(endpoint)

            try:
                root = codec.deserialize(plaintext)
            except Exception:
                continue

            if not root:
                continue

            packet = root[0]
            tl_type = packet.get("@type", "")

            if "packetContents" in tl_type:
                if peer_state is not None:
                    self._update_peer_state(peer_state, packet)

                for msg in self._extract_messages(packet):
                    self._dispatch_message(msg)
            else:
                self._dispatch_message(packet)
