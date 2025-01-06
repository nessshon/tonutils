from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class DeviceInfo:
    """
    Represents information about a device associated with a wallet.
    """
    platform: str
    app_name: str
    app_version: str
    max_protocol_version: int
    features: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"DeviceInfo(platform={self.platform}, "
            f"app_name={self.app_name}, "
            f"app_version={self.app_version}, "
            f"max_protocol_version={self.max_protocol_version}, "
            f"features={self.features})"
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DeviceInfo:
        """
        Creates a DeviceInfo instance from a dictionary.

        :param data: A dictionary containing device information.
        :return: An instance of DeviceInfo.
        """
        return cls(
            platform=data.get("platform", ""),
            app_name=data.get("appName", ""),
            app_version=data.get("appVersion", ""),
            max_protocol_version=data.get("maxProtocolVersion", 0),
            features=data.get("features", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the DeviceInfo instance into a dictionary.

        :return: A dictionary representation of the DeviceInfo.
        """
        return {
            "platform": self.platform,
            "appName": self.app_name,
            "appVersion": self.app_version,
            "maxProtocolVersion": self.max_protocol_version,
            "features": self.features,
        }
