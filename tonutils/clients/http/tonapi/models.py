import typing as t

from pydantic import BaseModel

from tonutils.types import ContractState


class BlockchainMessagePayload(BaseModel):
    """Payload for /blockchain/message endpoint."""

    boc: str


class BlockchainConfigResult(BaseModel):
    """Result model for /blockchain/config."""

    raw: t.Optional[str] = None


class BlockchainAccountResult(BaseModel):
    """Result model for /blockchain/accounts/{address}."""

    balance: int = 0
    status: str = ContractState.NONEXIST.value
    code: t.Optional[str] = None
    data: t.Optional[str] = None
    last_transaction_lt: t.Optional[int] = None
    last_transaction_hash: t.Optional[str] = None


class _BlockchainAccountTransaction(BaseModel):
    """Single account transaction with raw BoC payload."""

    raw: t.Optional[str] = None


class BlockchainAccountTransactionsResult(BaseModel):
    """Result model for /blockchain/accounts/{address}/transactions."""

    transactions: t.Optional[t.List[_BlockchainAccountTransaction]] = None


class BlockchainAccountMethodResult(BaseModel):
    """Result model for /blockchain/accounts/{address}/methods/{method_name}."""

    stack: t.Optional[t.List[t.Any]] = None
