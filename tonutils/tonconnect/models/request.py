import typing as t

from pydantic import Field, TypeAdapter, field_serializer, field_validator

from tonutils.tonconnect.models._types import A, BaseModel, OptionalChainId
from tonutils.tonconnect.models.payload import SignDataPayload, SendTransactionPayload

TParam = t.TypeVar("TParam")


class RpcRequestBase(BaseModel):
    """Base for all TonConnect RPC requests.

    Attributes:
        id: Request identifier, or `None`.
        method: RPC method name.
    """

    id: t.Optional[str] = None
    method: str = ""

    def to_bytes(self, **kwargs: t.Any) -> bytes:
        """Serialize the request to UTF-8 JSON bytes."""
        return self.dump_json(**kwargs).encode()


class RpcRequestWithParams(RpcRequestBase, t.Generic[TParam]):
    """RPC request carrying a typed `params` list.

    Attributes:
        params: Typed parameter list.
    """

    _params_adapter: t.ClassVar[TypeAdapter]

    params: t.List[TParam]

    @classmethod
    def _dump_param(cls, param: TParam) -> str:
        """Serialize a single param to a JSON string."""
        raw = cls._params_adapter.dump_json(param, by_alias=True, exclude_none=True)
        return raw.decode()

    @classmethod
    def _load_param(cls, raw: t.Any) -> TParam:
        """Deserialize a single param from JSON or dict."""
        if isinstance(raw, str):
            return cls._params_adapter.validate_json(raw)
        return cls._params_adapter.validate_python(raw)

    @field_validator("params", mode="before")
    @classmethod
    def _v_params(cls, v: t.Any) -> t.List[TParam]:
        if v is None:
            return []
        if not isinstance(v, list):
            raise TypeError("params must be a list")
        return [cls._load_param(item) for item in v]

    @field_serializer("params")
    def _s_params(self, v: t.List[TParam]) -> t.List[str]:
        return [self._dump_param(item) for item in v]


class TonAddressItem(BaseModel):
    """Connect request item for TON address.

    Attributes:
        name: Item type literal.
        network: Target network, or `None`.
    """

    name: t.Literal["ton_addr"] = "ton_addr"
    network: OptionalChainId = None


class TonProofItem(BaseModel):
    """Connect request item for TON Proof.

    Attributes:
        name: Item type literal.
        payload: Challenge payload string.
    """

    name: t.Literal["ton_proof"] = "ton_proof"
    payload: str


ConnectItem: t.TypeAlias = t.Annotated[
    t.Union[TonAddressItem, TonProofItem],
    Field(discriminator="name"),  # type: ignore
]


class ConnectRequest(BaseModel):
    """TonConnect connect request.

    Attributes:
        manifest_url: URL to `tonconnect-manifest.json`.
        items: Requested connect items.
    """

    manifest_url: str = A("manifestUrl")
    items: t.List[ConnectItem]


class DisconnectRpcRequest(RpcRequestBase):
    """RPC request to disconnect the wallet.

    Attributes:
        method: RPC method literal.
        params: Empty parameter list.
    """

    method: t.Literal["disconnect"] = "disconnect"
    params: t.List[t.Any] = Field(default_factory=list, min_length=0, max_length=0)


class SendTransactionRpcRequest(RpcRequestWithParams[SendTransactionPayload]):
    """RPC request to send a transaction.

    Attributes:
        method: RPC method literal.
        params: Transaction payloads.
    """

    _params_adapter = TypeAdapter(SendTransactionPayload)

    method: t.Literal["sendTransaction"] = "sendTransaction"
    params: t.List[SendTransactionPayload]


class SignDataRpcRequest(RpcRequestWithParams[SignDataPayload]):
    """RPC request to sign data.

    Attributes:
        method: RPC method literal.
        params: Sign data payloads.
    """

    _params_adapter = TypeAdapter(SignDataPayload)

    method: t.Literal["signData"] = "signData"
    params: t.List[SignDataPayload]


RpcRequests: t.TypeAlias = t.Annotated[
    t.Union[
        DisconnectRpcRequest,
        SendTransactionRpcRequest,
        SignDataRpcRequest,
    ],
    Field(discriminator="method"),  # type: ignore
]

AppMessage: t.TypeAlias = t.Union[
    ConnectRequest,
    RpcRequests,
]
