from __future__ import annotations

import typing as t
from dataclasses import dataclass

from tonutils.types import BaseModel


@dataclass
class BlockchainMessagePayload:
    """Payload for /blockchain/message endpoint."""

    boc: str


@dataclass
class BlockchainConfigResult(BaseModel):
    """Result model for /blockchain/config."""

    raw: str | None = None


@dataclass
class BlockchainAccountResult(BaseModel):
    """Result model for /blockchain/accounts/{address}."""

    balance: int = 0
    """Account balance in nanotons."""

    status: str = "nonexist"
    """Account lifecycle status string."""

    code: str | None = None
    """Hex-encoded contract code BoC, or ``None``."""

    data: str | None = None
    """Hex-encoded contract data BoC, or ``None``."""

    last_transaction_lt: int | None = None
    """Logical time of last transaction, or ``None``."""

    last_transaction_hash: str | None = None
    """Hash of last transaction, or ``None``."""


@dataclass
class BlockchainAccountTransaction(BaseModel):
    """Single account transaction with raw BoC payload."""

    raw: str | None = None


@dataclass
class BlockchainAccountTransactionsResult(BaseModel):
    """Result model for /blockchain/accounts/{address}/transactions."""

    transactions: list[BlockchainAccountTransaction] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        raw_txs = data.get("transactions")
        if raw_txs is None:
            return cls()
        return cls(transactions=[
            BlockchainAccountTransaction.from_dict(item) if isinstance(item, dict) else item
            for item in raw_txs
        ])


@dataclass
class BlockchainAccountMethodResult(BaseModel):
    """Result model for /blockchain/accounts/{address}/methods/{method_name}."""

    exit_code: int
    """TVM exit code."""

    stack: list[t.Any] | None = None
    """TVM stack items, or ``None``."""

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        :raises ValueError: If ``exit_code`` is missing.
        """
        if "exit_code" not in data:
            raise ValueError("Missing required field: 'exit_code'")
        return cls(exit_code=data["exit_code"], stack=data.get("stack"))


@dataclass
class _GaslessGasJetton:
    """Supported gas jetton entry from gasless configuration."""

    master_id: str


@dataclass
class GaslessConfigResult(BaseModel):
    """Result model for /gasless/config."""

    relay_address: str
    """Address of the relay that pays gas."""

    gas_jettons: list[_GaslessGasJetton]
    """Supported jettons for gas payment."""

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        jettons = [
            _GaslessGasJetton(**item) if isinstance(item, dict) else item
            for item in data.get("gas_jettons", [])
        ]
        return cls(relay_address=data["relay_address"], gas_jettons=jettons)


@dataclass
class GaslessEstimatePayload:
    """Payload for /gasless/estimate/{master_id}."""

    return_emulation: bool
    """Whether to return emulation result."""

    wallet_address: str
    """Sender wallet address string."""

    wallet_public_key: str
    """Hex-encoded sender public key."""

    messages: list[BlockchainMessagePayload]
    """BoC-encoded messages to estimate."""


@dataclass
class GaslessSignRawMessage(BaseModel):
    """Single message returned by gasless estimation."""

    address: str
    """Destination address string."""

    amount: str
    """Amount in nanotons as string."""

    payload: str | None = None
    """Base64-encoded message payload, or ``None``."""

    state_init: str | None = None
    """Base64-encoded StateInit, or ``None``."""

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        return cls(
            address=data["address"],
            amount=data["amount"],
            payload=data.get("payload"),
            state_init=data.get("stateInit") or data.get("state_init"),
        )

    def to_dict(self) -> dict[str, t.Any]:
        """Convert to dictionary.

        :return: JSON-serializable dictionary.
        """
        return {
            "address": self.address,
            "amount": self.amount,
            "payload": self.payload,
            "stateInit": self.state_init,
        }


@dataclass
class GaslessEstimateResult(BaseModel):
    """Result model for /gasless/estimate/{master_id}."""

    protocol_name: str
    """Gasless protocol name (e.g. ``gasless``)."""

    relay_address: str
    """Address of the relay that pays gas."""

    commission: str
    """Relay commission amount as string."""

    from_: str
    """Sender address (JSON key ``from``)."""

    valid_until: int
    """Expiration unix timestamp for the transaction."""

    messages: list[GaslessSignRawMessage]
    """Messages to sign and send."""

    emulation: dict[str, t.Any] | None = None
    """Emulation result, or ``None``."""

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        messages = [
            GaslessSignRawMessage.from_dict(item) if isinstance(item, dict) else item
            for item in data.get("messages", [])
        ]
        return cls(
            protocol_name=data["protocol_name"],
            relay_address=data["relay_address"],
            commission=data["commission"],
            from_=data.get("from") or data.get("from_", ""),
            valid_until=data["valid_until"],
            messages=messages,
            emulation=data.get("emulation"),
        )

    def to_dict(self) -> dict[str, t.Any]:
        """Convert to dictionary.

        :return: JSON-serializable dictionary.
        """
        return {
            "protocol_name": self.protocol_name,
            "relay_address": self.relay_address,
            "commission": self.commission,
            "from": self.from_,
            "valid_until": self.valid_until,
            "messages": [m.to_dict() for m in self.messages],
            "emulation": self.emulation,
        }


@dataclass
class GaslessSendPayload:
    """Payload for /gasless/send."""

    wallet_public_key: str
    """Hex-encoded sender public key."""

    boc: str
    """Hex-encoded signed external message BoC."""
