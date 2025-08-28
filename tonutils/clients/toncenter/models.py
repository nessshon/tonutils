import typing as t
from typing import Any

from pydantic import BaseModel

from ...types import ContractState
from ...utils import cell_to_b64, to_cell


class SendBocPayload(BaseModel):
    boc: str

    def model_post_init(self, context: Any, /) -> None:
        cell = to_cell(self.boc)
        self.boc = cell_to_b64(cell)


class _Config(BaseModel):
    bytes: t.Optional[str] = None


class _ConfigAll(BaseModel):
    config: t.Optional[_Config] = None


class GetConfigAllResult(BaseModel):
    result: t.Optional[_ConfigAll] = None


class _LastTransactionID(BaseModel):
    lt: t.Optional[str] = None
    hash: t.Optional[str] = None


class _AddressInformation(BaseModel):
    balance: int = 0
    state: t.Optional[str] = ContractState.UNINIT.value
    code: t.Optional[str] = None
    data: t.Optional[str] = None
    last_transaction_id: t.Optional[_LastTransactionID] = None

    def model_post_init(self, _: t.Any) -> None:
        if self.state == "uninitialized":
            self.state = "uninit"


class GetAddressInformationResult(BaseModel):
    result: _AddressInformation = _AddressInformation()


class _Transaction(BaseModel):
    data: t.Optional[str] = None


class GetTransactionResult(BaseModel):
    result: t.Optional[t.List[_Transaction]] = None


class _GetMethod(BaseModel):
    stack: t.List[t.Any]


class RunGetMethodPayload(BaseModel):
    address: str
    method: str
    stack: t.List[t.Any]


class RunGetMethodResul(BaseModel):
    result: t.Optional[_GetMethod] = None
