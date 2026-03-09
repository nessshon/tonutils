import typing as t

from pydantic import BaseModel, Field, ConfigDict

from tonutils.types import ContractState
from tonutils.utils import to_cell, cell_to_b64


class BlockchainMessagePayload(BaseModel):
    """Payload for /blockchain/message endpoint."""

    boc: str


class BlockchainConfigResult(BaseModel):
    """Result model for /blockchain/config."""

    raw: t.Optional[str] = None


class BlockchainAccountResult(BaseModel):
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
    status: str = ContractState.NONEXIST.value
    code: t.Optional[str] = None
    data: t.Optional[str] = None
    last_transaction_lt: t.Optional[int] = None
    last_transaction_hash: t.Optional[str] = None


class BlockchainAccountTransaction(BaseModel):
    """Single account transaction with raw BoC payload."""

    raw: t.Optional[str] = None


class BlockchainAccountTransactionsResult(BaseModel):
    """Result model for /blockchain/accounts/{address}/transactions."""

    transactions: t.Optional[t.List[BlockchainAccountTransaction]] = None


class BlockchainAccountMethodResult(BaseModel):
    """Result model for /blockchain/accounts/{address}/methods/{method_name}.

    Attributes:
        stack: TVM stack items, or `None`.
        exit_code: TVM exit code.
    """

    stack: t.Optional[t.List[t.Any]] = None
    exit_code: int


class _GaslessGasJetton(BaseModel):
    """Supported gas jetton entry from gasless configuration."""

    master_id: str


class GaslessConfigResult(BaseModel):
    """Result model for /gasless/config.

    Attributes:
        relay_address: Address of the relay that pays gas.
        gas_jettons: Supported jettons for gas payment.
    """

    relay_address: str
    gas_jettons: t.List[_GaslessGasJetton]


class GaslessEstimatePayload(BaseModel):
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


class GaslessSignRawMessage(BaseModel):
    """Single message returned by gasless estimation.

    Attributes:
        address: Destination address string.
        amount: Amount in nanotons as string.
        payload: Base64-encoded message payload, or `None`.
        state_init: Base64-encoded StateInit, or `None`.
    """

    address: str
    amount: str
    payload: t.Optional[str] = Field(default=None)
    state_init: t.Optional[str] = Field(alias="stateInit", default=None)

    model_config = ConfigDict(populate_by_name=True)


class GaslessEstimateResult(BaseModel):
    """Result model for /gasless/estimate/{master_id}.

    Attributes:
        protocol_name: Gasless protocol name (e.g. ``gasless``).
        relay_address: Address of the relay that pays gas.
        commission: Relay commission amount as string.
        from_: Sender address (aliased from ``from``).
        valid_until: Expiration unix timestamp for the transaction.
        messages: Messages to sign and send.
        emulation: Emulation result, or `None`.
    """

    protocol_name: str
    relay_address: str
    commission: str
    from_: str = Field(alias="from")
    valid_until: int
    messages: t.List[GaslessSignRawMessage]
    emulation: t.Optional[t.Dict[str, t.Any]] = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class GaslessSendPayload(BaseModel):
    """Payload for /gasless/send.

    Attributes:
        wallet_public_key: Hex-encoded sender public key.
        boc: Hex-encoded signed external message BoC.
    """

    wallet_public_key: str
    boc: str


class SendBocPayload(BaseModel):
    """Payload for /sendBoc endpoint.

    Normalizes input to base64-encoded BoC string during post-init.
    """

    boc: str

    def model_post_init(self, context: t.Any, /) -> None:
        """Convert input BoC into base64 BoC."""
        cell = to_cell(self.boc)
        self.boc = cell_to_b64(cell)


class Config(BaseModel):
    """Wrapper for base64-encoded config cell."""

    bytes: t.Optional[str] = None


class ConfigAll(BaseModel):
    """Wrapper for config section returned by Toncenter."""

    config: t.Optional[Config] = None


class GetConfigAllResult(BaseModel):
    """Result model for /getConfigAll."""

    result: t.Optional[ConfigAll] = None


class LastTransactionID(BaseModel):
    """Last transaction identification."""

    lt: t.Optional[str] = None
    hash: t.Optional[str] = None


class _AddressInformation(BaseModel):
    """Parsed contract state from Toncenter.

    Normalizes legacy state name `uninitialized` to `uninit`.
    """

    balance: int = 0
    state: t.Optional[str] = ContractState.UNINIT.value
    code: t.Optional[str] = None
    data: t.Optional[str] = None
    last_transaction_id: t.Optional[LastTransactionID] = None

    def model_post_init(self, _: t.Any) -> None:
        """Normalize legacy Toncenter state names."""
        if self.state == "uninitialized":
            self.state = "uninit"


class GetAddressInformationResult(BaseModel):
    """Result wrapper for /getAddressInformation."""

    result: _AddressInformation = _AddressInformation()


class Transaction(BaseModel):
    """Minimal transaction model containing raw BoC data."""

    data: t.Optional[str] = None


class GetTransactionsResult(BaseModel):
    """Result wrapper for /getTransactions."""

    result: t.Optional[t.List[Transaction]] = None


class GetMethod(BaseModel):
    """Container for TVM stack result.

    Attributes:
        stack: TVM stack items.
        exit_code: TVM exit code.
    """

    stack: t.List[t.Any]
    exit_code: int


class RunGetMethodPayload(BaseModel):
    """Request payload for /runGetMethod.

    Attributes:
        address: Contract address string.
        method: Get-method name.
        stack: Encoded TVM stack arguments.
    """

    address: str
    method: str
    stack: t.List[t.Any]


class RunGetMethodResult(BaseModel):
    """Response wrapper for /runGetMethod."""

    result: t.Optional[GetMethod] = None
