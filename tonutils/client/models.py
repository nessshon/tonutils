from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pytoniq_core import Address


@dataclass
class AddressBookEntry:
    user_friendly: Address
    domain: Optional[str] = None
    interfaces: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "AddressBookEntry":
        return cls(
            user_friendly=Address(data["user_friendly"]),
            domain=data.get("domain"),
            interfaces=data.get("interfaces", []),
        )


@dataclass
class JettonWalletInfo:
    address: Address
    balance: int
    owner: Address
    jetton: Address
    code_hash: str
    data_hash: str
    last_transaction_lt: int

    @classmethod
    def from_dict(cls, data: dict) -> "JettonWalletInfo":
        return cls(
            address=Address(data["address"]),
            balance=int(data["balance"]),
            owner=Address(data["owner"]),
            jetton=Address(data["jetton"]),
            code_hash=data["code_hash"],
            data_hash=data["data_hash"],
            last_transaction_lt=int(data["last_transaction_lt"]),
        )


@dataclass
class TokenInfo:
    type: str
    valid: bool
    extra: Dict[str, Any] = field(default_factory=dict)
    name: Optional[str] = None
    symbol: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "TokenInfo":
        return cls(
            type=data["type"],
            valid=data["valid"],
            extra=data.get("extra", {}),
            name=data.get("name"),
            symbol=data.get("symbol"),
            description=data.get("description"),
            image=data.get("image"),
        )


@dataclass
class MetadataEntry:
    is_indexed: bool
    token_info: List[TokenInfo] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "MetadataEntry":
        return cls(
            is_indexed=data["is_indexed"],
            token_info=[TokenInfo.from_dict(t) for t in data.get("token_info", [])],
        )


@dataclass
class JettonWalletsResponse:
    jetton_wallets: List[JettonWalletInfo]
    address_book: Dict[str, AddressBookEntry]
    metadata: Dict[str, MetadataEntry]

    @classmethod
    def from_dict(cls, data: dict) -> "JettonWalletsResponse":
        return cls(
            jetton_wallets=[
                JettonWalletInfo.from_dict(w)
                for w in data.get("jetton_wallets", [])
            ],
            address_book={
                k: AddressBookEntry.from_dict(v)
                for k, v in data.get("address_book", {}).items()
            },
            metadata={
                k: MetadataEntry.from_dict(v)
                for k, v in data.get("metadata", {}).items()
            },
        )