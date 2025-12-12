from __future__ import annotations

import base64
import typing as t
from enum import Enum

from nacl.signing import SigningKey
from pytoniq_core import Address, Cell, StateInit, Slice

__all__ = [
    "ADNL",
    "AddressLike",
    "BagID",
    "Binary",
    "BinaryLike",
    "ClientType",
    "ContractState",
    "ContractStateInfo",
    "DEFAULT_SENDMODE",
    "DEFAULT_SUBWALLET_ID",
    "DNSCategory",
    "DNSPrefix",
    "MetadataPrefix",
    "NetworkGlobalID",
    "PrivateKey",
    "PublicKey",
    "SendMode",
    "StackItem",
    "StackItems",
    "StackTag",
    "WorkchainID",
]

AddressLike = t.Union[Address, str]
"""Type alias for TON address inputs. Accepts either an Address object or string representation."""

BinaryLike = t.Union[str, int, bytes]
"""Type alias for binary data inputs. Accepts string (hex/base64), integer, or raw bytes."""

StackItem = t.Optional[t.Union[int, Cell, Slice, Address]]
"""Type alias for a single TVM stack item. Can be an integer, Cell, Slice, Address, or None."""

StackItems = t.List[t.Union[StackItem, t.List[StackItem]]]
"""Type alias for TVM stack items list. Supports nested lists for tuple representation."""


class ClientType(str, Enum):
    """
    TON blockchain client connection types.

    Attributes:
        ADNL: Abstract Datagram Network Layer protocol connection
        HTTP: HTTP-based API connection (e.g., Toncenter)
    """

    ADNL = "adnl"
    HTTP = "http"


class NetworkGlobalID(int, Enum):
    """
    TON blockchain network identifiers.

    Attributes:
        MAINNET: Production network (-239)
        TESTNET: Testing network (-3)
    """

    MAINNET = -239
    TESTNET = -3


class WorkchainID(int, Enum):
    """
    TON blockchain workchain identifiers.

    Attributes:
        BASECHAIN: Default workchain for user contracts (0)
        MASTERCHAIN: Coordination workchain for validators and configuration (-1)
    """

    BASECHAIN = 0
    MASTERCHAIN = -1


class MetadataPrefix(int, Enum):
    """
    Jetton/NFT metadata storage location prefixes.

    Attributes:
        ONCHAIN: Metadata stored directly on blockchain (0)
        OFFCHAIN: Metadata stored off-chain with URI reference (1)
    """

    ONCHAIN = 0
    OFFCHAIN = 1


class SendMode(int, Enum):
    """
    Message sending modes for TON transactions.

    Attributes:
        CARRY_ALL_REMAINING_BALANCE: Send all remaining balance (128)
        CARRY_ALL_REMAINING_INCOMING_VALUE: Forward all remaining incoming value (64)
        DESTROY_ACCOUNT_IF_ZERO: Destroy account if balance becomes zero (32)
        BOUNCE_IF_ACTION_FAIL: Bounce transaction on action phase failure (16)
        IGNORE_ERRORS: Continue execution despite errors (2)
        PAY_GAS_SEPARATELY: Pay forward fees separately from message value (1)
        DEFAULT: Standard mode with no special flags (0)
    """

    CARRY_ALL_REMAINING_BALANCE = 128
    CARRY_ALL_REMAINING_INCOMING_VALUE = 64
    DESTROY_ACCOUNT_IF_ZERO = 32
    BOUNCE_IF_ACTION_FAIL = 16
    IGNORE_ERRORS = 2
    PAY_GAS_SEPARATELY = 1
    DEFAULT = 0


class DNSPrefix(int, Enum):
    """
    TON DNS record type prefixes.

    Attributes:
        DNS_NEXT_RESOLVER: Pointer to next resolver contract (0xBA93)
        STORAGE: TON Storage bag ID reference (0x7473)
        WALLET: Wallet address reference (0x9FD3)
        SITE: ADNL address for TON Sites (0xAD01)
    """

    DNS_NEXT_RESOLVER = 0xBA93
    STORAGE = 0x7473
    WALLET = 0x9FD3
    SITE = 0xAD01


class DNSCategory(int, Enum):
    """
    TON DNS record categories as SHA-256.

    Attributes:
        DNS_NEXT_RESOLVER: Hash for next resolver queries
        STORAGE: Hash for storage bag ID queries
        WALLET: Hash for wallet address queries
        SITE: Hash for site ADNL address queries
        ALL: Query all categories (0)
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
    """
    TON smart contract lifecycle states.

    Attributes:
        ACTIVE: Contract is deployed and operational
        FROZEN: Contract is frozen (storage fees debt)
        UNINIT: Contract address exists but code not deployed
        NONEXIST: Contract address has no balance or state
    """

    ACTIVE = "active"
    FROZEN = "frozen"
    UNINIT = "uninit"
    NONEXIST = "nonexist"


class ContractStateInfo:
    """
    TON smart contract state information.

    Attributes:
        code_raw: Base64-encoded BoC of contract code
        data_raw: Base64-encoded BoC of contract data
        balance: Contract balance in nanotons
        state: Current lifecycle state
        last_transaction_lt: Logical time of last transaction
        last_transaction_hash: Hash of last transaction
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
        self.code_raw = code_raw
        self.data_raw = data_raw
        self.balance = balance
        self.state = state
        self.last_transaction_lt = last_transaction_lt
        self.last_transaction_hash = last_transaction_hash

    @property
    def code(self) -> t.Optional[Cell]:
        """Parsed Cell object from code_raw."""
        return Cell.one_from_boc(self.code_raw) if self.code_raw else None

    @property
    def data(self) -> t.Optional[Cell]:
        """Parsed Cell object from data_raw."""
        return Cell.one_from_boc(self.data_raw) if self.data_raw else None

    @property
    def state_init(self) -> StateInit:
        """StateInit object combining code and data."""
        return StateInit(code=self.code, data=self.data)

    def __repr__(self) -> str:
        parts = " ".join(f"{k}: {v!r}" for k, v in vars(self).items())
        return f"< {self.__class__.__name__} {parts} >"


class StackTag(str, Enum):
    """TVM stack value type tags."""

    NUM = "num"
    NULL = "null"
    CELL = "cell"
    SLICE = "slice"
    TUPLE = "tuple"
    LIST = "list"
    TVM_CELL = "tvm.Cell"
    TVM_SLICE = "tvm.Slice"

    @classmethod
    def of(cls, v: t.Any) -> StackTag:
        type_map = {
            int: cls.NUM,
            list: cls.LIST,
            tuple: cls.TUPLE,
            Cell: cls.CELL,
            Slice: cls.SLICE,
            Address: cls.SLICE,
        }
        return type_map.get(type(v), cls.NULL)


class Binary:
    """Binary data wrapper with multiple format support."""

    def __init__(self, raw: BinaryLike, size: int = 32) -> None:
        """
        :param raw: Input data (bytes, int, hex string, or base64 string)
        :param size: Expected byte length (default: 32)
        """
        self._size = size
        self._bytes = self._parse(raw)

    @property
    def size(self) -> int:
        """Expected byte length of the binary data."""
        return self._size

    def _parse(self, value: t.Any) -> bytes:
        """Parse input value into bytes."""
        if isinstance(value, bytes):
            return value
        if isinstance(value, int):
            length = max(1, (value.bit_length() + 7) // 8)
            return value.to_bytes(length, "big")
        if isinstance(value, str):
            s = value.strip()
            if s.lower().startswith("0x"):
                return int(s, 16).to_bytes(self._size, "big")
            try:
                return base64.b64decode(s)
            except (Exception,):
                n = int(s, 10)
                length = max(1, (n.bit_length() + 7) // 8)
                return n.to_bytes(length, "big")
        raise ValueError(f"Invalid binary type: {type(value).__name__}.")

    @property
    def as_bytes(self) -> bytes:
        """Binary data as bytes."""
        return self._bytes.rjust(self._size, b"\x00")

    @property
    def as_int(self) -> int:
        """Binary data as integer."""
        return int.from_bytes(self.as_bytes, byteorder="big")

    @property
    def as_hex(self) -> str:
        """Binary data as hex string."""
        return self.as_bytes.hex()

    @property
    def as_b64(self) -> str:
        """Binary data as base64 string."""
        return base64.b64encode(self.as_bytes).decode()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Binary) and self.as_bytes == other.as_bytes

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.as_b64!r}>"


class PublicKey(Binary):
    """Ed25519 public key (32 bytes)."""

    def __init__(self, raw: BinaryLike) -> None:
        """
        :param raw: 32-byte public key data
        """
        super().__init__(raw, size=32)


class PrivateKey(Binary):
    """Ed25519 private key with automatic public key derivation."""

    def __init__(self, raw: BinaryLike) -> None:
        """
        :param raw: 32-byte seed or 64-byte keypair
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
        """Get the derived public key."""
        return PublicKey(self._public_part)

    @property
    def keypair(self) -> Binary:
        """Get the full 64-byte keypair (private + public)."""
        raw = self.as_bytes + self.public_key.as_bytes
        return Binary(raw, size=64)


class ADNL(Binary):
    """Abstract Datagram Network Layer address (32 bytes)."""

    def __init__(self, raw: BinaryLike) -> None:
        """
        :param raw: 32-byte ADNL address
        """
        super().__init__(raw, 32)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.as_hex.upper()}>"


class BagID(ADNL):
    """TON Storage bag identifier (32 bytes)."""


DEFAULT_SUBWALLET_ID = 698983191
"""Default subwallet ID for wallet contracts."""

DEFAULT_SENDMODE = SendMode.PAY_GAS_SEPARATELY | SendMode.IGNORE_ERRORS
"""Default send mode: pay fees separately and ignore errors."""
