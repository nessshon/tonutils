import typing as t

from pydantic import Field

from tonutils.tonconnect.models._types import A, BaseModel


class SendTransactionFeature(BaseModel):
    """Wallet `SendTransaction` feature declaration.

    Attributes:
        name: Feature name literal.
        max_messages: Maximum outgoing messages, or `None`.
        extra_currency_supported: Whether extra currencies are supported.
    """

    name: t.Literal["SendTransaction"]
    max_messages: t.Optional[int] = A("maxMessages", default=None)
    extra_currency_supported: bool = A("extraCurrencySupported", default=False)


class SignDataFeature(BaseModel):
    """Wallet `SignData` feature declaration.

    Attributes:
        name: Feature name literal.
        types: Supported payload types.
    """

    name: t.Literal["SignData"]
    types: t.List[t.Literal["binary", "cell", "text"]]


FeatureType: t.TypeAlias = t.Annotated[
    t.Union[SendTransactionFeature, SignDataFeature],
    Field(discriminator="name"),  # type: ignore
]
FeatureTypes = t.List[FeatureType]
