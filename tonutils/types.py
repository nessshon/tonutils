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
BinaryLike = t.Union[str, int, bytes]
StackItem = t.Optional[t.Union[int, Cell, Slice, Address]]
StackItems = t.List[t.Union[StackItem, t.List[StackItem]]]


class ClientType(str, Enum):
    ADNL = "adnl"
    HTTP = "http"


class NetworkGlobalID(int, Enum):
    MAINNET = -239
    TESTNET = -3


class WorkchainID(int, Enum):
    BASECHAIN = 0
    MASTERCHAIN = -1


class MetadataPrefix(int, Enum):
    ONCHAIN = 0
    OFFCHAIN = 1


class SendMode(int, Enum):
    CARRY_ALL_REMAINING_BALANCE = 128
    CARRY_ALL_REMAINING_INCOMING_VALUE = 64
    DESTROY_ACCOUNT_IF_ZERO = 32
    BOUNCE_IF_ACTION_FAIL = 16
    IGNORE_ERRORS = 2
    PAY_GAS_SEPARATELY = 1
    DEFAULT = 0


class DNSPrefix(int, Enum):
    DNS_NEXT_RESOLVER = 0xBA93
    STORAGE = 0x7473
    WALLET = 0x9FD3
    SITE = 0xAD01


class DNSCategory(int, Enum):
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
    ACTIVE = "active"
    FROZEN = "frozen"
    UNINIT = "uninit"
    NONEXIST = "nonexist"


class ContractStateInfo:

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
        return Cell.one_from_boc(self.code_raw) if self.code_raw else None

    @property
    def data(self) -> t.Optional[Cell]:
        return Cell.one_from_boc(self.data_raw) if self.data_raw else None

    @property
    def state_init(self) -> StateInit:
        return StateInit(code=self.code, data=self.data)

    def __repr__(self) -> str:
        parts = " ".join(f"{k}: {v!r}" for k, v in vars(self).items())
        return f"< {self.__class__.__name__} {parts} >"


class StackTag(str, Enum):
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

    def __init__(self, raw: BinaryLike, size: int = 32) -> None:
        self._size = size
        self._bytes = self._parse(raw)

    @property
    def size(self) -> int:
        return self._size

    def _parse(self, value: t.Union[t.Any]) -> bytes:
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
        return self._bytes.rjust(self._size, b"\x00")

    @property
    def as_int(self) -> int:
        return int.from_bytes(self.as_bytes, byteorder="big")

    @property
    def as_hex(self) -> str:
        return self.as_bytes.hex()

    @property
    def as_b64(self) -> str:
        return base64.b64encode(self.as_bytes).decode()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Binary) and self.as_bytes == other.as_bytes

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.as_b64!r}>"


class PublicKey(Binary):

    def __init__(self, raw: BinaryLike) -> None:
        super().__init__(raw, size=32)


class PrivateKey(Binary):

    def __init__(self, raw: BinaryLike) -> None:
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
        return PublicKey(self._public_part)

    @property
    def keypair(self) -> Binary:
        raw = self.as_bytes + self.public_key.as_bytes
        return Binary(raw, size=64)


class ADNL(Binary):

    def __init__(self, raw: BinaryLike) -> None:
        super().__init__(raw, 32)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}<{self.as_hex.upper()}>"


class BagID(ADNL): ...


DEFAULT_SUBWALLET_ID = 698983191
DEFAULT_SENDMODE = SendMode.PAY_GAS_SEPARATELY | SendMode.IGNORE_ERRORS
