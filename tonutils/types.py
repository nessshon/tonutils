from __future__ import annotations

import typing as t
from dataclasses import asdict, dataclass, fields
from enum import Enum

from ton_core import BlockIdExt, BlockRef, Cell, ContractState, StateInit

from tonutils.exceptions import CDN_CHALLENGE_MARKERS

__all__ = [
    "DEFAULT_ADNL_RETRY_POLICY",
    "DEFAULT_HTTP_RETRY_POLICY",
    "BaseModel",
    "ClientType",
    "ContractInfo",
    "MasterchainInfo",
    "RetryPolicy",
    "RetryRule",
]


@dataclass(init=False)
class BaseModel:
    """Base dataclass with ``from_dict`` / ``to_dict`` serialization."""

    def __init__(self, **kwargs: t.Any) -> None:
        for key, value in kwargs.items():
            object.__setattr__(self, key, value)

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create an instance from a dictionary, picking only known fields.

        :param data: Raw dictionary (e.g. API response).
        :return: New instance.
        """
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})

    def to_dict(self) -> dict[str, t.Any]:
        """Serialize to a plain dictionary.

        :return: Dictionary of field names to values.
        """
        return asdict(self)


class ClientType(str, Enum):
    """TON blockchain client connection type."""

    ADNL = "adnl"
    """Abstract Datagram Network Layer protocol connection."""

    HTTP = "http"
    """HTTP-based API connection (e.g., Toncenter)."""


class ContractInfo:
    """TON smart-contract on-chain state snapshot."""

    def __init__(
        self,
        code_raw: str | None = None,
        data_raw: str | None = None,
        balance: int = 0,
        state: ContractState = ContractState.NONEXIST,
        last_transaction_lt: int | None = None,
        last_transaction_hash: str | None = None,
    ) -> None:
        """Initialize contract info.

        :param code_raw: Base64-encoded BoC of contract code.
        :param data_raw: Base64-encoded BoC of contract data.
        :param balance: Contract balance in nanotons.
        :param state: Current lifecycle state.
        :param last_transaction_lt: Logical time of last transaction.
        :param last_transaction_hash: Hash of last transaction.
        """
        self.code_raw = code_raw
        self.data_raw = data_raw
        self.balance = balance
        self.state = state
        self.last_transaction_lt = last_transaction_lt
        self.last_transaction_hash = last_transaction_hash

    @property
    def code(self) -> Cell | None:
        """Parsed ``Cell`` from ``code_raw``, or ``None`` if absent."""
        return Cell.one_from_boc(self.code_raw) if self.code_raw else None

    @property
    def data(self) -> Cell | None:
        """Parsed ``Cell`` from ``data_raw``, or ``None`` if absent."""
        return Cell.one_from_boc(self.data_raw) if self.data_raw else None

    @property
    def state_init(self) -> StateInit:
        """``StateInit`` combining ``code`` and ``data``."""
        return StateInit(code=self.code, data=self.data)

    def __repr__(self) -> str:
        """Return a human-readable representation of the contract info.

        :return: String with all field values.
        """
        parts = " ".join(f"{k}: {v!r}" for k, v in vars(self).items())
        return f"< {self.__class__.__name__} {parts} >"


@dataclass(slots=True, frozen=True)
class RetryRule:
    """Retry rule matched by error code and/or message substrings.

    If ``codes`` is set, code must be in ``codes``.
    If ``markers`` is set, any marker must appear in message (case-insensitive).
    If both are set, both conditions must match.
    """

    attempts: int = 3
    """Maximum retry attempts (>= 1)."""

    base_delay: float = 0.3
    """Initial delay in seconds (>= 0)."""

    cap_delay: float = 3.0
    """Maximum delay in seconds (>= base_delay)."""

    codes: tuple[int, ...] | None = None
    """Error codes this rule applies to, or ``None``."""

    markers: tuple[str, ...] | None = None
    """Case-insensitive substrings for message matching, or ``None``."""

    def __post_init__(self) -> None:
        """Validate fields and normalize ``markers`` to lowercase.

        :raises ValueError: If constraints on fields are violated.
        """
        if self.attempts < 1:
            raise ValueError("attempts must be >= 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.cap_delay < 0:
            raise ValueError("cap_delay must be >= 0")
        if self.cap_delay < self.base_delay:
            raise ValueError("cap_delay must be >= base_delay")
        if self.markers:
            norm = tuple(m.strip().lower() for m in self.markers if m and m.strip())
            object.__setattr__(self, "markers", norm or None)

    def matches(self, code: int, message: t.Any) -> bool:
        """Test whether this rule matches the given error.

        :param code: Error or status code.
        :param message: Error message.
        :return: ``True`` if the rule matches.
        """
        if self.codes is not None and code not in self.codes:
            return False

        if self.markers:
            msg = str(message or "").lower()
            if not any(m in msg for m in self.markers):
                return False

        return True

    def delay(self, attempt_index: int) -> float:
        """Calculate delay before retry using exponential back-off.

        :param attempt_index: Zero-based attempt index.
        :return: Delay in seconds.
        :raises ValueError: If attempt_index < 0.
        """
        if attempt_index < 0:
            raise ValueError("attempt_index must be >= 0")
        d = self.base_delay * (2**attempt_index)
        return d if d < self.cap_delay else self.cap_delay


@dataclass(slots=True, frozen=True)
class RetryPolicy:
    """Ordered collection of ``RetryRule`` instances (first match wins)."""

    rules: tuple[RetryRule, ...]
    """Retry rules evaluated in order."""

    def rule_for(self, code: int, message: t.Any) -> RetryRule | None:
        """Return the first matching rule, or ``None``.

        :param code: Error or status code.
        :param message: Error message.
        :return: Matching ``RetryRule`` or ``None``.
        """
        for r in self.rules:
            if r.matches(code, message):
                return r
        return None


DEFAULT_HTTP_RETRY_POLICY = RetryPolicy(
    rules=(
        # rate limit exceed
        RetryRule(
            codes=(429,),
            attempts=3,
            base_delay=0.3,
            cap_delay=3.0,
        ),
        # transient gateway/service failures
        RetryRule(
            codes=(502, 503, 504),
            attempts=3,
            base_delay=0.5,
            cap_delay=5.0,
        ),
        # CDN/protection/challenge pages (Cloudflare, etc.)
        RetryRule(
            attempts=3,
            base_delay=1.0,
            cap_delay=8.0,
            markers=tuple(CDN_CHALLENGE_MARKERS.keys()),
        ),
    )
)
"""Default retry policy for HTTP queries."""

DEFAULT_ADNL_RETRY_POLICY = RetryPolicy(
    rules=(
        # rate limit exceed
        RetryRule(codes=(228, 5556), attempts=3),
        # block (...) is not in db
        RetryRule(codes=(651,), attempts=4),
        # backend node timeout
        RetryRule(codes=(502,), attempts=5),
    )
)
"""Default retry policy for ADNL queries."""


@dataclass
class MasterchainInfo:
    """TON masterchain state information."""

    last: BlockRef
    """Latest masterchain block."""

    init: BlockRef
    """Genesis / initialization block."""

    state_root_hash: str
    """Base64-encoded root hash of current state."""

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> MasterchainInfo:
        """Create from a TL response dictionary.

        Strips ``@type`` and parses nested block dicts into ``BlockRef``.

        :param data: Raw TL response dictionary.
        :return: Parsed ``MasterchainInfo``.
        """
        last = data["last"]
        init = data["init"]
        return cls(
            last=BlockRef.from_dict(last) if isinstance(last, dict) else last,
            init=BlockRef.from_dict(init) if isinstance(init, dict) else init,
            state_root_hash=data["state_root_hash"],
        )

    @staticmethod
    def _parse_raw_block(b: BlockRef) -> BlockIdExt:
        """Convert ``BlockRef`` to ``BlockIdExt``.

        :param b: Block reference to convert.
        :return: Parsed ``BlockIdExt``.
        """
        return BlockIdExt.from_dict(asdict(b))

    def last_block(self) -> BlockIdExt:
        """Return the latest masterchain block as ``BlockIdExt``."""
        return self._parse_raw_block(self.last)

    def init_block(self) -> BlockIdExt:
        """Return the genesis block as ``BlockIdExt``."""
        return self._parse_raw_block(self.init)
