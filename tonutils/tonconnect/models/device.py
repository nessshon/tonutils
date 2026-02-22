import typing as t

from pydantic import Field, TypeAdapter, field_validator

from tonutils.tonconnect.models._types import A, BaseModel
from tonutils.tonconnect.models.feature import FeatureType, FeatureTypes

_FEATURE_ADAPTER = TypeAdapter(FeatureType)


class Device(BaseModel):
    """Wallet device information from the connect event.

    Attributes:
        platform: Device platform identifier.
        app_name: Wallet application name.
        app_version: Wallet application version.
        max_protocol_version: Maximum supported TonConnect protocol version.
        features: Declared wallet features.
    """

    platform: str
    app_name: str = A("appName")
    app_version: str = A("appVersion")
    max_protocol_version: int = A("maxProtocolVersion")
    features: FeatureTypes = Field(default_factory=list)

    @field_validator("features", mode="before")
    @classmethod
    def _v_features(cls, v: t.Any) -> FeatureTypes:
        return [_FEATURE_ADAPTER.validate_python(f) for f in v if isinstance(f, dict)]
