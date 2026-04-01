from __future__ import annotations

import hashlib
import time
import typing as t
from dataclasses import dataclass, field
from enum import Enum

from ton_core import Binary, BinaryLike, PublicKey

__all__ = [
    "Bucket",
    "Continuation",
    "DhtKey",
    "DhtKeyDescription",
    "DhtNode",
    "DhtUpdateRule",
    "DhtValue",
    "KeyLike",
    "PriorityList",
    "affinity",
    "compute_key_id",
    "normalize_key",
    "normalize_pub_key",
]

KeyLike = bytes | str | Binary
"""Key input: raw ``bytes``, hex ``str``, ``Binary`` subclass (e.g. ``ADNL``)."""


def normalize_key(key: KeyLike) -> bytes:
    """Normalize a key to ``bytes``.

    :param key: 256-bit key in any supported format.
    :return: Raw 32-byte key.
    """
    if isinstance(key, Binary):
        return key.as_bytes
    if isinstance(key, str):
        return bytes.fromhex(key)
    return key


def normalize_pub_key(key: BinaryLike) -> bytes:
    """Normalize a public key to ``bytes``.

    :param key: Public key as ``bytes``, hex ``str``, base64 ``str``, or ``int``.
    :return: Raw 32-byte public key.
    """
    if isinstance(key, bytes):
        return key
    return PublicKey(key).as_bytes


def affinity(x: bytes, y: bytes) -> int:
    """Count leading zero bits of ``XOR(x, y)``.

    :param x: First 256-bit identifier (32 bytes).
    :param y: Second 256-bit identifier (32 bytes).
    :return: Number of leading zero bits in the XOR result (0..256).
    """
    xor_int = int.from_bytes(x[:32], "big") ^ int.from_bytes(y[:32], "big")
    if xor_int == 0:
        return 256
    return 256 - xor_int.bit_length()


def compute_key_id(pub_key: bytes) -> bytes:
    """Compute ADNL key ID from Ed25519 public key.

    ``SHA-256(pub.ed25519 TL constructor LE + key)``.

    :param pub_key: Ed25519 public key (32 bytes).
    :return: 32-byte key ID.
    """
    type_id = b"\xc6\xb4\x13\x48"
    return hashlib.sha256(type_id + pub_key).digest()


class DhtUpdateRule(str, Enum):
    """DHT key update rule identifiers."""

    SIGNATURE = "dht.updateRule.signature"
    ANYBODY = "dht.updateRule.anybody"
    OVERLAY_NODES = "dht.updateRule.overlayNodes"


@dataclass(slots=True, frozen=True)
class DhtKey:
    """DHT key used for store/lookup operations."""

    id: bytes
    """256-bit key owner identifier (ADNL address)."""

    name: bytes
    """Key name (e.g. ``b"address"``)."""

    idx: int = 0
    """Key index (usually 0)."""

    def __init__(self, id: bytes | str, name: bytes | str, idx: int = 0) -> None:
        object.__setattr__(self, "id", bytes.fromhex(id) if isinstance(id, str) else id)
        object.__setattr__(self, "name", name.encode() if isinstance(name, str) else name)
        object.__setattr__(self, "idx", idx)

    @property
    def key_id(self) -> bytes:
        """SHA-256 hash of the TL-serialized ``dht.key``, used as lookup target."""
        _dht_key_tl_id = b"\x8f\xde\x67\xf6"
        name_tl = self._tl_encode_bytes(self.name)
        data = _dht_key_tl_id + self.id + name_tl + self.idx.to_bytes(4, "little")
        return hashlib.sha256(data).digest()

    @staticmethod
    def _tl_encode_bytes(value: bytes) -> bytes:
        """Encode bytes in TL format with 4-byte alignment padding."""
        n = len(value)
        if n < 254:
            prefix = n.to_bytes(1, "big")
            total = 1 + n
        else:
            prefix = b"\xfe" + n.to_bytes(3, "little")
            total = 4 + n
        padding_len = (4 - (total % 4)) % 4
        return prefix + value + b"\x00" * padding_len


@dataclass(slots=True, frozen=True)
class DhtKeyDescription:
    """DHT key descriptor with ownership proof."""

    key: DhtKey
    id_public_key: bytes
    update_rule: DhtUpdateRule
    signature: bytes = b""


@dataclass(slots=True)
class DhtValue:
    """DHT stored value with key descriptor and TTL."""

    key_description: DhtKeyDescription
    value: bytes | dict[str, t.Any]
    ttl: int
    signature: bytes = b""
    raw_value: bytes = b""
    """Original raw bytes before deserialization (used by codec for signature verification)."""

    @property
    def expired(self) -> bool:
        """Whether the value has expired."""
        return self.ttl < int(time.time())


class DhtNode:
    """DHT node with health tracking.

    Tracks ``bad_score`` and ``ping`` latency for bucket sorting
    and priority list selection.
    """

    _MAX_FAIL_COUNT: t.ClassVar[int] = 3

    def __init__(
        self,
        *,
        adnl_id: bytes,
        addr: str,
        server_key: bytes,
    ) -> None:
        self._adnl_id = adnl_id
        self._addr = addr
        self._server_key = server_key
        self._bad_score: int = 0
        self._ping: int = 0
        self._in_fly_queries: int = 0

    @property
    def adnl_id(self) -> bytes:
        """Return the ADNL identifier of this node."""
        return self._adnl_id

    @property
    def addr(self) -> str:
        """Return the network address of this node."""
        return self._addr

    @property
    def server_key(self) -> bytes:
        """Return the server public key."""
        return self._server_key

    @property
    def bad_score(self) -> int:
        """Return the current failure score of this node."""
        return self._bad_score

    @property
    def ping(self) -> int:
        """Return the last measured ping latency in milliseconds."""
        return self._ping

    @ping.setter
    def ping(self, value: int) -> None:
        """Set the ping latency in milliseconds."""
        self._ping = value

    @property
    def in_fly_queries(self) -> int:
        """Return the number of currently in-flight queries."""
        return self._in_fly_queries

    def inc_in_fly(self) -> None:
        """Increment the in-flight query counter."""
        self._in_fly_queries += 1

    def dec_in_fly(self) -> int:
        """Decrement the in-flight query counter and return the new value."""
        self._in_fly_queries = max(0, self._in_fly_queries - 1)
        return self._in_fly_queries

    @property
    def id(self) -> str:
        """ADNL key ID as hex string."""
        return self._adnl_id.hex()

    def update_status(self, is_good: bool) -> None:
        """Update the node health status after a query attempt."""
        if is_good:
            self._bad_score = 0
        else:
            if self._bad_score < self._MAX_FAIL_COUNT:
                self._bad_score += 1

    def sort_key(self) -> tuple[int, int]:
        """Return a tuple of (bad_score, ping) for bucket sorting."""
        return self._bad_score, self._ping

    def __repr__(self) -> str:
        return f"< DhtNode addr: {self._addr} bad_score: {self._bad_score} ping: {self._ping}ms >"


class Bucket:
    """Kademlia bucket with capacity ``k * 5``, sorted by health."""

    def __init__(self, k: int) -> None:
        self._capacity = k * 5
        self._nodes: list[DhtNode] = []

    def add_node(self, node: DhtNode) -> None:
        """Add or replace a node in the bucket, maintaining sorted order."""
        for i, existing in enumerate(self._nodes):
            if existing.adnl_id == node.adnl_id:
                self._nodes[i] = node
                self._sort()
                return
        self._nodes.append(node)
        self._sort()
        if len(self._nodes) > self._capacity:
            self._nodes = self._nodes[: self._capacity]

    def find_node(self, adnl_id: bytes) -> DhtNode | None:
        """Find a node by its ADNL ID, or return ``None``."""
        for node in self._nodes:
            if node.adnl_id == adnl_id:
                return node
        return None

    def get_nodes(self) -> list[DhtNode]:
        """Return a shallow copy of all nodes in the bucket."""
        return list(self._nodes)

    def _sort(self) -> None:
        self._nodes.sort(key=lambda n: n.sort_key())

    def __len__(self) -> int:
        return len(self._nodes)


class PriorityList:
    """Fixed-size, affinity-sorted node list with ``used`` tracking."""

    def __init__(self, max_len: int, target_id: bytes) -> None:
        self._max_len = max_len
        self._target_id = target_id
        self._nodes: list[DhtNode] = []
        self._used: dict[str, bool] = {}

    def add(self, node: DhtNode) -> bool:
        """Add a node if it improves the list.

        Go parity: only resets ``used`` if priority actually improved.
        """
        node_id = node.id
        node_aff = affinity(node.adnl_id, self._target_id)

        if node_id in self._used:
            for i, existing in enumerate(self._nodes):
                if existing.id == node_id:
                    existing_aff = affinity(existing.adnl_id, self._target_id)
                    if node_aff <= existing_aff:
                        return False
                    self._nodes[i] = node
                    self._used[node_id] = False
                    self._sort()
                    return True
            return False

        if len(self._nodes) >= self._max_len:
            worst = self._nodes[-1]
            worst_aff = affinity(worst.adnl_id, self._target_id)
            if node_aff <= worst_aff:
                return False
            evicted = self._nodes.pop()
            self._used.pop(evicted.id, None)

        self._nodes.append(node)
        self._used[node_id] = False
        self._sort()
        return True

    def get(self) -> tuple[DhtNode | None, int]:
        """Return the next unused node and the best affinity in the list."""
        best_aff = self.get_best_affinity()
        for node in self._nodes:
            if not self._used.get(node.id, True):
                self._used[node.id] = True
                return node, best_aff
        return None, best_aff

    def get_best_affinity(self) -> int:
        """Return the highest affinity value among all nodes."""
        if not self._nodes:
            return 0
        return affinity(self._nodes[0].adnl_id, self._target_id)

    def mark_used(self, node: DhtNode, used: bool) -> None:
        """Go parity: ``MarkUsed`` calls ``Add`` first."""
        self.add(node)
        node_id = node.id
        if node_id in self._used:
            self._used[node_id] = used

    def _sort(self) -> None:
        self._nodes.sort(
            key=lambda n: affinity(n.adnl_id, self._target_id),
            reverse=True,
        )

    def __len__(self) -> int:
        return len(self._nodes)


@dataclass
class Continuation:
    """Carries state between iterative DHT lookup rounds."""

    checked_nodes: list[DhtNode] = field(default_factory=list)
