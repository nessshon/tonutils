import typing as t

from pydantic import BaseModel

from tonutils.types import ContractState
from tonutils.utils import to_cell, cell_to_b64


class SendBocPayload(BaseModel):
    """
    Payload for /sendBoc endpoint.

    Normalizes input to base64-encoded BoC string during post-init.
    """

    boc: str

    def model_post_init(self, context: t.Any, /) -> None:
        """Convert input BoC (hex/base64/Cell/Slice) into base64 BoC."""
        cell = to_cell(self.boc)
        self.boc = cell_to_b64(cell)


class _Config(BaseModel):
    """Wrapper for base64-encoded config cell."""

    bytes: t.Optional[str] = None


class _ConfigAll(BaseModel):
    """Wrapper for config section returned by Toncenter."""

    config: t.Optional[_Config] = None


class GetConfigAllResult(BaseModel):
    """Result model for /getConfigAll."""

    result: t.Optional[_ConfigAll] = None


class _LastTransactionID(BaseModel):
    """Last transaction identification."""

    lt: t.Optional[str] = None
    hash: t.Optional[str] = None


class _AddressInformation(BaseModel):
    """
    Parsed contract state information.

    Normalizes Toncenter-specific fields such as "uninitialized".
    """

    balance: int = 0
    state: t.Optional[str] = ContractState.UNINIT.value
    code: t.Optional[str] = None
    data: t.Optional[str] = None
    last_transaction_id: t.Optional[_LastTransactionID] = None

    def model_post_init(self, _: t.Any) -> None:
        """Normalize legacy Toncenter state names."""
        if self.state == "uninitialized":
            self.state = "uninit"


class GetAddressInformationResult(BaseModel):
    """Typed result wrapper for /getAddressInformation."""

    result: _AddressInformation = _AddressInformation()


class _Transaction(BaseModel):
    """Minimal transaction model containing raw BoC data."""

    data: t.Optional[str] = None


class GetTransactionResult(BaseModel):
    """Result wrapper for /getTransactions."""

    result: t.Optional[t.List[_Transaction]] = None


class _GetMethod(BaseModel):
    """Container for TVM stack array."""

    stack: t.List[t.Any]


class RunGetMethodPayload(BaseModel):
    """Request payload for /runGetMethod."""

    address: str
    method: str
    stack: t.List[t.Any]


class RunGetMethodResul(BaseModel):
    """Response wrapper for /runGetMethod."""

    result: t.Optional[_GetMethod] = None
