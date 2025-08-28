import typing as t

from pydantic import BaseModel

from ...types import ContractState


class BlockchainMessagePayload(BaseModel):
    boc: str


class BlockchainConfigResult(BaseModel):
    raw: t.Optional[str] = None


class BlockchainAccountResult(BaseModel):
    balance: int = 0
    status: str = ContractState.NONEXIST.value
    code: t.Optional[str] = None
    data: t.Optional[str] = None
    last_transaction_lt: t.Optional[int] = None
    last_transaction_hash: t.Optional[str] = None


class _BlockchainAccountTransaction(BaseModel):
    raw: t.Optional[str] = None


class BlockchainAccountTransactionsResult(BaseModel):
    transactions: t.Optional[t.List[_BlockchainAccountTransaction]] = None


class BlockchainAccountMethodResult(BaseModel):
    stack: t.Optional[t.List[t.Any]] = None
