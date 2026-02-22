import typing as t

from pydantic import Field

from tonutils.tonconnect.models._types import A, BaseModel
from tonutils.tonconnect.models.feature import FeatureTypes


class JSBridgeType(BaseModel):
    """JS-bridge connection descriptor.

    Attributes:
        type: Bridge type literal.
        key: JS-bridge injection key.
    """

    type: t.Literal["js"]
    key: str


class SSEBridgeType(BaseModel):
    """SSE-bridge connection descriptor.

    Attributes:
        type: Bridge type literal.
        url: SSE bridge URL.
    """

    type: t.Literal["sse"]
    url: str


BridgeType: t.TypeAlias = t.Annotated[
    t.Union[JSBridgeType, SSEBridgeType],
    Field(discriminator="type"),  # type: ignore
]
BridgeTypes = t.List[BridgeType]


class AppWallet(BaseModel):
    """Wallet application descriptor from the wallets catalogue.

    Attributes:
        name: Display name.
        image: Icon URL.
        app_name: Machine-readable application name.
        bridge: Supported bridge types.
        tondns: TON DNS name, or `None`.
        about_url: About page URL, or `None`.
        universal_url: Universal link base, or `None`.
        deep_link: Deep link scheme, or `None`.
        platforms: Supported platform identifiers.
        features: Declared wallet features.
    """

    name: str
    image: str
    app_name: str
    bridge: BridgeTypes
    tondns: t.Optional[str] = None
    about_url: t.Optional[str] = None
    universal_url: t.Optional[str] = None
    deep_link: t.Optional[str] = A("deepLink", default=None)

    platforms: t.List[str]
    features: FeatureTypes

    @property
    def bridge_url(self) -> t.Optional[str]:
        """First SSE bridge URL, or `None`."""
        for b in self.bridge:
            if b.type == "sse":
                return b.url
        return None


AppWallets = t.List[AppWallet]
