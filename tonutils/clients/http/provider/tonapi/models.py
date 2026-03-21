from __future__ import annotations

import typing as t
from dataclasses import dataclass, fields


@dataclass
class BlockchainMessagePayload:
    """Payload for /blockchain/message endpoint."""

    boc: str


@dataclass
class BlockchainConfigResult:
    """Result model for /blockchain/config."""

    raw: t.Optional[str] = None

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> BlockchainConfigResult:
        return cls(raw=data.get("raw"))


@dataclass
class BlockchainAccountResult:
    """Result model for /blockchain/accounts/{address}.

    Attributes:
        balance: Account balance in nanotons.
        status: Account lifecycle status string.
        code: Hex-encoded contract code BoC, or `None`.
        data: Hex-encoded contract data BoC, or `None`.
        last_transaction_lt: Logical time of last transaction, or `None`.
        last_transaction_hash: Hash of last transaction, or `None`.
    """

    balance: int = 0
    status: str = "nonexist"
    code: t.Optional[str] = None
    data: t.Optional[str] = None
    last_transaction_lt: t.Optional[int] = None
    last_transaction_hash: t.Optional[str] = None

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> BlockchainAccountResult:
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in names})


@dataclass
class BlockchainAccountTransaction:
    """Single account transaction with raw BoC payload."""

    raw: t.Optional[str] = None


@dataclass
class BlockchainAccountTransactionsResult:
    """Result model for /blockchain/accounts/{address}/transactions."""

    transactions: t.Optional[t.List[BlockchainAccountTransaction]] = None

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> BlockchainAccountTransactionsResult:
        raw_txs = data.get("transactions")
        if raw_txs is None:
            return cls()
        return cls(transactions=[
            BlockchainAccountTransaction(**item) if isinstance(item, dict) else item
            for item in raw_txs
        ])


@dataclass
class BlockchainAccountMethodResult:
    """Result model for /blockchain/accounts/{address}/methods/{method_name}.

    Attributes:
        stack: TVM stack items, or `None`.
        exit_code: TVM exit code.
    """

    exit_code: int
    stack: t.Optional[t.List[t.Any]] = None

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> BlockchainAccountMethodResult:
        if "exit_code" not in data:
            raise ValueError("Missing required field: 'exit_code'")
        return cls(exit_code=data["exit_code"], stack=data.get("stack"))


@dataclass
class _GaslessGasJetton:
    """Supported gas jetton entry from gasless configuration."""

    master_id: str


@dataclass
class GaslessConfigResult:
    """Result model for /gasless/config.

    Attributes:
        relay_address: Address of the relay that pays gas.
        gas_jettons: Supported jettons for gas payment.
    """

    relay_address: str
    gas_jettons: t.List[_GaslessGasJetton]

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> GaslessConfigResult:
        jettons = [
            _GaslessGasJetton(**item) if isinstance(item, dict) else item
            for item in data.get("gas_jettons", [])
        ]
        return cls(relay_address=data["relay_address"], gas_jettons=jettons)


@dataclass
class GaslessEstimatePayload:
    """Payload for /gasless/estimate/{master_id}.

    Attributes:
        return_emulation: Whether to return emulation result.
        wallet_address: Sender wallet address string.
        wallet_public_key: Hex-encoded sender public key.
        messages: BoC-encoded messages to estimate.
    """

    return_emulation: bool
    wallet_address: str
    wallet_public_key: str
    messages: t.List[BlockchainMessagePayload]


@dataclass
class GaslessSignRawMessage:
    """Single message returned by gasless estimation.

    Attributes:
        address: Destination address string.
        amount: Amount in nanotons as string.
        payload: Base64-encoded message payload, or `None`.
        state_init: Base64-encoded StateInit, or `None`.
    """

    address: str
    amount: str
    payload: t.Optional[str] = None
    state_init: t.Optional[str] = None

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> GaslessSignRawMessage:
        return cls(
            address=data["address"],
            amount=data["amount"],
            payload=data.get("payload"),
            state_init=data.get("stateInit") or data.get("state_init"),
        )

    def to_dict(self) -> t.Dict[str, t.Any]:
        return {
            "address": self.address,
            "amount": self.amount,
            "payload": self.payload,
            "stateInit": self.state_init,
        }


@dataclass
class GaslessEstimateResult:
    """Result model for /gasless/estimate/{master_id}.

    Attributes:
        protocol_name: Gasless protocol name (e.g. ``gasless``).
        relay_address: Address of the relay that pays gas.
        commission: Relay commission amount as string.
        from_: Sender address (JSON key ``from``).
        valid_until: Expiration unix timestamp for the transaction.
        messages: Messages to sign and send.
        emulation: Emulation result, or `None`.
    """

    protocol_name: str
    relay_address: str
    commission: str
    from_: str
    valid_until: int
    messages: t.List[GaslessSignRawMessage]
    emulation: t.Optional[t.Dict[str, t.Any]] = None

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> GaslessEstimateResult:
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

    def to_dict(self) -> t.Dict[str, t.Any]:
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
    """Payload for /gasless/send.

    Attributes:
        wallet_public_key: Hex-encoded sender public key.
        boc: Hex-encoded signed external message BoC.
    """

    wallet_public_key: str
    boc: str
