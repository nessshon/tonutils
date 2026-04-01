from __future__ import annotations

import typing as t
from dataclasses import dataclass

from ton_core import ContractState, cell_to_b64, to_cell

from tonutils.types import BaseModel


@dataclass
class SendBocPayload:
    """Payload for /sendBoc endpoint.

    Normalizes input to base64-encoded BoC string during post-init.
    """

    boc: str

    def __post_init__(self) -> None:
        """Normalize ``boc`` to a base64-encoded BoC string."""
        cell = to_cell(self.boc)
        self.boc = cell_to_b64(cell)


@dataclass
class Config(BaseModel):
    """Wrapper for base64-encoded config cell."""

    bytes: str | None = None


@dataclass
class ConfigAll(BaseModel):
    """Wrapper for config section returned by Toncenter."""

    config: Config | None = None

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        config_raw = data.get("config")
        config = Config.from_dict(config_raw) if isinstance(config_raw, dict) else config_raw
        return cls(config=config)


@dataclass
class GetConfigAllResult(BaseModel):
    """Result model for /getConfigAll."""

    result: ConfigAll | None = None

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        result_raw = data.get("result")
        if result_raw is None:
            return cls()
        result = ConfigAll.from_dict(result_raw) if isinstance(result_raw, dict) else result_raw
        return cls(result=result)


@dataclass
class LastTransactionID(BaseModel):
    """Last transaction identification."""

    lt: str | None = None
    hash: str | None = None


@dataclass
class _AddressInformation(BaseModel):
    """Parsed contract state from Toncenter.

    Normalizes legacy state name ``uninitialized`` to ``uninit``.
    """

    balance: int = 0
    state: str | None = ContractState.UNINIT.value
    code: str | None = None
    data: str | None = None
    last_transaction_id: LastTransactionID | None = None

    def __post_init__(self) -> None:
        """Normalize legacy ``uninitialized`` state to ``uninit``."""
        if self.state == "uninitialized":
            self.state = "uninit"

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        ltid_raw = data.get("last_transaction_id")
        ltid = LastTransactionID.from_dict(ltid_raw) if isinstance(ltid_raw, dict) else ltid_raw
        return cls(
            balance=data.get("balance", 0),
            state=data.get("state", ContractState.UNINIT.value),
            code=data.get("code"),
            data=data.get("data"),
            last_transaction_id=ltid,
        )


@dataclass
class GetAddressInformationResult(BaseModel):
    """Result wrapper for /getAddressInformation."""

    result: _AddressInformation

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        result_raw = data.get("result", {})
        result = (
            _AddressInformation.from_dict(result_raw)
            if isinstance(result_raw, dict)
            else result_raw
        )
        return cls(result=result)


@dataclass
class Transaction(BaseModel):
    """Minimal transaction model containing raw BoC data."""

    data: str | None = None


@dataclass
class GetTransactionsResult(BaseModel):
    """Result wrapper for /getTransactions."""

    result: list[Transaction] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        raw_list = data.get("result")
        if raw_list is None:
            return cls()
        return cls(result=[
            Transaction.from_dict(item) if isinstance(item, dict) else item
            for item in raw_list
        ])


@dataclass
class GetMethod(BaseModel):
    """Container for TVM stack result."""

    stack: list[t.Any]
    """TVM stack items."""

    exit_code: int
    """TVM exit code."""


@dataclass
class RunGetMethodPayload:
    """Request payload for /runGetMethod."""

    address: str
    """Contract address string."""

    method: str
    """Get-method name."""

    stack: list[t.Any]
    """Encoded TVM stack arguments."""


@dataclass
class RunGetMethodResult(BaseModel):
    """Response wrapper for /runGetMethod."""

    result: GetMethod | None = None

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> t.Any:
        """Create from dictionary.

        :param data: Raw API response dictionary.
        :return: Parsed instance.
        """
        result_raw = data.get("result")
        if result_raw is None:
            return cls()
        result = GetMethod.from_dict(result_raw) if isinstance(result_raw, dict) else result_raw
        return cls(result=result)
