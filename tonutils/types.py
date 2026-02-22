from __future__ import annotations

import base64
import re
import typing as t
from contextlib import suppress
from dataclasses import dataclass
from enum import Enum

from nacl.signing import SigningKey
from pytoniq_core import Address, Cell, StateInit

__all__ = [
    "ADNL",
    "AddressLike",
    "BagID",
    "Binary",
    "BinaryLike",
    "ClientType",
    "ContractState",
    "ContractInfo",
    "DNSCategory",
    "DNSPrefix",
    "MetadataPrefix",
    "NetworkGlobalID",
    "PrivateKey",
    "PublicKey",
    "RetryPolicy",
    "RetryRule",
    "SendMode",
    "WorkchainID",
    "DEFAULT_ADNL_RETRY_POLICY",
    "DEFAULT_HTTP_RETRY_POLICY",
    "DEFAULT_SENDMODE",
    "DEFAULT_SUBWALLET_ID",
    "MAINNET_GENESIS_UTIME",
    "MASTERCHAIN_SHARD",
]

from tonutils.exceptions import CDN_CHALLENGE_MARKERS

AddressLike = t.Union[Address, str]
"""TON address: `Address` object or string representation."""

BinaryLike = t.Union[str, int, bytes]
"""Binary data input: hex/base64 string, integer, or raw bytes."""


class ClientType(str, Enum):
    """TON blockchain client connection type.

    Attributes:
        ADNL: Abstract Datagram Network Layer protocol connection.
        HTTP: HTTP-based API connection (e.g., Toncenter).
    """

    ADNL = "adnl"
    HTTP = "http"


class NetworkGlobalID(int, Enum):
    """TON blockchain network identifier.

    Attributes:
        MAINNET: Production network (-239).
        TESTNET: Testing network (-3).
    """

    MAINNET = -239
    TESTNET = -3


class WorkchainID(int, Enum):
    """TON blockchain workchain identifier.

    Attributes:
        BASECHAIN: Default workchain for user contracts (0).
        MASTERCHAIN: Coordination workchain for validators and configuration (-1).
    """

    BASECHAIN = 0
    MASTERCHAIN = -1


class MetadataPrefix(int, Enum):
    """Jetton/NFT metadata storage location prefix.

    Attributes:
        ONCHAIN: Metadata stored directly on-chain (0).
        OFFCHAIN: Metadata stored off-chain with URI reference (1).
    """

    ONCHAIN = 0
    OFFCHAIN = 1


class SendMode(int, Enum):
    """Message sending mode flags for TON transactions.

    Attributes:
        CARRY_ALL_REMAINING_BALANCE: Send all remaining balance (128).
        CARRY_ALL_REMAINING_INCOMING_VALUE: Forward all remaining incoming value (64).
        DESTROY_ACCOUNT_IF_ZERO: Destroy account if balance reaches zero (32).
        BOUNCE_IF_ACTION_FAIL: Bounce transaction on action-phase failure (16).
        IGNORE_ERRORS: Continue execution despite errors (2).
        PAY_GAS_SEPARATELY: Pay forward fees separately from message value (1).
        DEFAULT: Standard mode with no special flags (0).
    """

    CARRY_ALL_REMAINING_BALANCE = 128
    CARRY_ALL_REMAINING_INCOMING_VALUE = 64
    DESTROY_ACCOUNT_IF_ZERO = 32
    BOUNCE_IF_ACTION_FAIL = 16
    IGNORE_ERRORS = 2
    PAY_GAS_SEPARATELY = 1
    DEFAULT = 0


class DNSPrefix(int, Enum):
    """TON DNS record type prefix.

    Attributes:
        DNS_NEXT_RESOLVER: Pointer to next resolver contract (0xBA93).
        STORAGE: TON Storage bag-ID reference (0x7473).
        WALLET: Wallet address reference (0x9FD3).
        SITE: ADNL address for TON Sites (0xAD01).
    """

    DNS_NEXT_RESOLVER = 0xBA93
    STORAGE = 0x7473
    WALLET = 0x9FD3
    SITE = 0xAD01


class DNSCategory(int, Enum):
    """TON DNS record category as SHA-256 hash.

    Attributes:
        DNS_NEXT_RESOLVER: Hash for next-resolver queries.
        STORAGE: Hash for storage bag-ID queries.
        WALLET: Hash for wallet address queries.
        SITE: Hash for site ADNL address queries.
        ALL: Query all categories (0).
    """

    DNS_NEXT_RESOLVER = (
        11732114750494247458678882651681748623800183221773167493832867265755123357695
    )
    STORAGE = (
        33305727148774590499946634090951755272001978043137765208040544350030765946327
    )
    WALLET = (
        105311596331855300602201538317979276640056460191511695660591596829410056223515
    )
    SITE = (
        113837984718866553357015413641085683664993881322709313240352703269157551621118
    )
    ALL = 0


class ContractState(str, Enum):
    """TON smart-contract lifecycle state.

    Attributes:
        ACTIVE: Deployed and operational.
        FROZEN: Frozen due to storage-fee debt.
        UNINIT: Address exists but code is not deployed.
        NONEXIST: No balance or state.
    """

    ACTIVE = "active"
    FROZEN = "frozen"
    UNINIT = "uninit"
    NONEXIST = "nonexist"


class ContractInfo:
    """TON smart-contract on-chain state snapshot.

    Attributes:
        code_raw: Base64-encoded BoC of contract code, or `None`.
        data_raw: Base64-encoded BoC of contract data, or `None`.
        balance: Contract balance in nanotons.
        state: Current lifecycle state.
        last_transaction_lt: Logical time of last transaction, or `None`.
        last_transaction_hash: Hash of last transaction, or `None`.
    """

    def __init__(
        self,
        code_raw: t.Optional[str] = None,
        data_raw: t.Optional[str] = None,
        balance: int = 0,
        state: ContractState = ContractState.NONEXIST,
        last_transaction_lt: t.Optional[int] = None,
        last_transaction_hash: t.Optional[str] = None,
    ) -> None:
        """
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
    def code(self) -> t.Optional[Cell]:
        """Parsed `Cell` from `code_raw`, or `None` if absent."""
        return Cell.one_from_boc(self.code_raw) if self.code_raw else None

    @property
    def data(self) -> t.Optional[Cell]:
        """Parsed `Cell` from `data_raw`, or `None` if absent."""
        return Cell.one_from_boc(self.data_raw) if self.data_raw else None

    @property
    def state_init(self) -> StateInit:
        """`StateInit` combining `code` and `data`."""
        return StateInit(code=self.code, data=self.data)

    def __repr__(self) -> str:
        parts = " ".join(f"{k}: {v!r}" for k, v in vars(self).items())
        return f"< {self.__class__.__name__} {parts} >"


class Binary:
    """Binary data wrapper with multi-format input/output.

    Accepts bytes, integers, hex strings (0x-prefixed or plain), base64
    strings, and decimal-integer strings.
    """

    def __init__(self, raw: BinaryLike, size: int = 32) -> None:
        """
        :param raw: Input data.
        :param size: Expected byte length (default: 32).
        """
        self._size = size
        self._bytes = self._parse(raw)

    @property
    def size(self) -> int:
        """Expected byte length."""
        return self._size

    def _parse(self, value: t.Any) -> bytes:
        if isinstance(value, bytes):
            return value
        if isinstance(value, int):
            length = max(1, (value.bit_length() + 7) // 8)
            return value.to_bytes(length, "big")

        if isinstance(value, str):
            s = value.strip()

            # 0x... hex
            if s.lower().startswith("0x"):
                return bytes.fromhex(s[2:])

            # plain hex (common case for publicKey)
            if len(s) % 2 == 0 and re.compile(r"^[0-9a-fA-F]+$").fullmatch(s):
                if len(s) == self._size * 2:
                    return bytes.fromhex(s)

            # base64 (strict)
            with suppress(Exception):
                b = base64.b64decode(s, validate=True)
                return b

            # decimal int as string fallback
            n = int(s, 10)
            length = max(1, (n.bit_length() + 7) // 8)
            return n.to_bytes(length, "big")

        raise ValueError(f"Invalid binary type: {type(value).__name__}.")

    @property
    def as_bytes(self) -> bytes:
        """Data as bytes, left-padded with zeros to `size`."""
        return self._bytes.rjust(self._size, b"\x00")

    @property
    def as_int(self) -> int:
        """Data as big-endian unsigned integer."""
        return int.from_bytes(self.as_bytes, byteorder="big")

    @property
    def as_hex(self) -> str:
        """Data as lowercase hex string."""
        return self.as_bytes.hex()

    @property
    def as_b64(self) -> str:
        """Data as base64-encoded string."""
        return base64.b64encode(self.as_bytes).decode()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Binary) and self.as_bytes == other.as_bytes

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.as_b64!r}>"


class PublicKey(Binary):
    """Ed25519 public key (32 bytes)."""

    def __init__(self, raw: BinaryLike) -> None:
        """
        :param raw: 32-byte public key data.
        """
        super().__init__(raw, size=32)


class PrivateKey(Binary):
    """Ed25519 private key with automatic public-key derivation.

    Accepts a 32-byte seed or a 64-byte keypair (private + public).
    """

    def __init__(self, raw: BinaryLike) -> None:
        """
        :param raw: 32-byte seed or 64-byte keypair.
        :raises ValueError: If parsed length is neither 32 nor 64 bytes.
        """
        raw_bytes = self._parse(raw)

        if len(raw_bytes) == 32:
            signing_key = SigningKey(raw_bytes)
            raw_bytes += signing_key.verify_key.encode()
        elif len(raw_bytes) == 64:
            pass
        else:
            raise ValueError("Private key must be 32 or 64 bytes.")

        self._public_part = raw_bytes[32:]
        super().__init__(raw_bytes[:32], size=32)

    @property
    def public_key(self) -> PublicKey:
        """Derived Ed25519 public key."""
        return PublicKey(self._public_part)

    @property
    def keypair(self) -> Binary:
        """Full 64-byte keypair (private + public)."""
        raw = self.as_bytes + self.public_key.as_bytes
        return Binary(raw, size=64)


class ADNL(Binary):
    """ADNL address (32 bytes)."""

    def __init__(self, raw: BinaryLike) -> None:
        """
        :param raw: 32-byte ADNL address.
        """
        super().__init__(raw, 32)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.as_hex.upper()}>"


class BagID(ADNL):
    """TON Storage bag identifier (32 bytes)."""


@dataclass(slots=True, frozen=True)
class RetryRule:
    """Retry rule matched by error code and/or message substrings.

    If `codes` is set, code must be in `codes`.
    If `markers` is set, any marker must appear in message (case-insensitive).
    If both are set, both conditions must match.

    Attributes:
        attempts: Maximum retry attempts (>= 1).
        base_delay: Initial delay in seconds (>= 0).
        cap_delay: Maximum delay in seconds (>= base_delay).
        codes: Error codes this rule applies to, or `None`.
        markers: Case-insensitive substrings for message matching, or `None`.
    """

    attempts: int = 3
    base_delay: float = 0.3
    cap_delay: float = 3.0

    codes: t.Optional[t.Tuple[int, ...]] = None
    markers: t.Optional[t.Tuple[str, ...]] = None

    def __post_init__(self) -> None:
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
        :return: `True` if the rule matches.
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
    """Ordered collection of `RetryRule` instances (first match wins).

    Attributes:
        rules: Retry rules evaluated in order.
    """

    rules: t.Tuple[RetryRule, ...]

    def rule_for(self, code: int, message: t.Any) -> t.Optional[RetryRule]:
        """Return the first matching rule, or `None`.

        :param code: Error or status code.
        :param message: Error message.
        :return: Matching `RetryRule` or `None`.
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

DEFAULT_SUBWALLET_ID = 698983191
"""Default subwallet ID for wallet contracts."""

DEFAULT_SENDMODE = SendMode.PAY_GAS_SEPARATELY | SendMode.IGNORE_ERRORS
"""Default send mode: pay fees separately and ignore errors."""

MASTERCHAIN_SHARD = -9223372036854775808
"""Shard identifier for the masterchain (-2^63)."""

MAINNET_GENESIS_UTIME = 1573822385
"""Unix timestamp of the TON mainnet genesis block (November 15, 2019)."""
