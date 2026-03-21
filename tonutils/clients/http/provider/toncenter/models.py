from __future__ import annotations

import typing as t
from dataclasses import dataclass

from tonutils.types import ContractState
from tonutils.utils import to_cell, cell_to_b64


@dataclass
class SendBocPayload:
    """Payload for /sendBoc endpoint.

    Normalizes input to base64-encoded BoC string during post-init.
    """

    boc: str

    def __post_init__(self) -> None:
        cell = to_cell(self.boc)
        self.boc = cell_to_b64(cell)


@dataclass
class Config:
    """Wrapper for base64-encoded config cell."""

    bytes: t.Optional[str] = None


@dataclass
class ConfigAll:
    """Wrapper for config section returned by Toncenter."""

    config: t.Optional[Config] = None


@dataclass
class GetConfigAllResult:
    """Result model for /getConfigAll."""

    result: t.Optional[ConfigAll] = None

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> GetConfigAllResult:
        result_raw = data.get("result")
        if result_raw is None:
            return cls()
        config_raw = result_raw.get("config") if isinstance(result_raw, dict) else None
        config = Config(**config_raw) if isinstance(config_raw, dict) else config_raw
        config_all = ConfigAll(config=config) if isinstance(result_raw, dict) else result_raw
        return cls(result=config_all)


@dataclass
class LastTransactionID:
    """Last transaction identification."""

    lt: t.Optional[str] = None
    hash: t.Optional[str] = None


@dataclass
class _AddressInformation:
    """Parsed contract state from Toncenter.

    Normalizes legacy state name ``uninitialized`` to ``uninit``.
    """

    balance: int = 0
    state: t.Optional[str] = ContractState.UNINIT.value
    code: t.Optional[str] = None
    data: t.Optional[str] = None
    last_transaction_id: t.Optional[LastTransactionID] = None

    def __post_init__(self) -> None:
        if self.state == "uninitialized":
            self.state = "uninit"

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> _AddressInformation:
        ltid_raw = data.get("last_transaction_id")
        ltid = LastTransactionID(**ltid_raw) if isinstance(ltid_raw, dict) else ltid_raw
        return cls(
            balance=data.get("balance", 0),
            state=data.get("state", ContractState.UNINIT.value),
            code=data.get("code"),
            data=data.get("data"),
            last_transaction_id=ltid,
        )


@dataclass
class GetAddressInformationResult:
    """Result wrapper for /getAddressInformation."""

    result: _AddressInformation

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> GetAddressInformationResult:
        result_raw = data.get("result", {})
        result = (
            _AddressInformation.from_dict(result_raw)
            if isinstance(result_raw, dict)
            else result_raw
        )
        return cls(result=result)


@dataclass
class Transaction:
    """Minimal transaction model containing raw BoC data."""

    data: t.Optional[str] = None


@dataclass
class GetTransactionsResult:
    """Result wrapper for /getTransactions."""

    result: t.Optional[t.List[Transaction]] = None

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> GetTransactionsResult:
        raw_list = data.get("result")
        if raw_list is None:
            return cls()
        return cls(result=[
            Transaction(**item) if isinstance(item, dict) else item
            for item in raw_list
        ])


@dataclass
class GetMethod:
    """Container for TVM stack result.

    Attributes:
        stack: TVM stack items.
        exit_code: TVM exit code.
    """

    stack: t.List[t.Any]
    exit_code: int


@dataclass
class RunGetMethodPayload:
    """Request payload for /runGetMethod.

    Attributes:
        address: Contract address string.
        method: Get-method name.
        stack: Encoded TVM stack arguments.
    """

    address: str
    method: str
    stack: t.List[t.Any]


@dataclass
class RunGetMethodResult:
    """Response wrapper for /runGetMethod."""

    result: t.Optional[GetMethod] = None

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> RunGetMethodResult:
        result_raw = data.get("result")
        if result_raw is None:
            return cls()
        result = GetMethod(**result_raw) if isinstance(result_raw, dict) else result_raw
        return cls(result=result)
