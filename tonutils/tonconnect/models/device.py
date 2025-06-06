from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ..utils.exceptions import WalletNotSupportFeatureError, TonConnectError
from ..utils.logger import logger

if TYPE_CHECKING:
    from . import WalletInfo, SignDataPayload


@dataclass
class DeviceInfo:
    """
    Represents information about a device associated with a wallet.
    """
    platform: str
    app_name: str
    app_version: str
    max_protocol_version: int
    features: List[Any] = field(default_factory=list)

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

    @classmethod
    def _find_feature(cls, features: List[Any], name: str) -> Optional[Dict[str, Any]]:
        return next(
            (feature for feature in features if isinstance(feature, dict) and feature.get("name") == name),
            None
        )

    @classmethod
    def _get_features(cls, wallet: WalletInfo) -> List[Any]:
        if wallet is None or wallet.device is None:
            logger.debug("Wallet or wallet device information is missing.")
            raise TonConnectError("Wallet or wallet device information is missing.")

        features = wallet.device.features
        if not isinstance(features, list):
            logger.debug("Invalid features format.")
            raise TonConnectError("Features must be a list.")

        return features

    def _verify_feature_supported(self, wallet: WalletInfo, feature_name: str) -> Dict[str, Any]:
        features = self._get_features(wallet)
        feature = self._find_feature(features, feature_name)

        if not feature:
            logger.debug(f"'{feature_name}' feature not supported.")
            raise WalletNotSupportFeatureError(f"Wallet does not support the '{feature_name}' feature.")

        return feature

    def verify_sign_data_feature(self, wallet: WalletInfo, payload: SignDataPayload) -> None:
        feature = self._verify_feature_supported(wallet, "SignData")
        supported_types = feature.get("types", [])

        if payload.type not in supported_types:
            logger.debug(
                f"Unsupported sign data type '{payload.type}'. Supported types: {supported_types}"
            )
            raise WalletNotSupportFeatureError(
                f"Wallet does not support signing data of type '{payload.type}'."
            )

    def verify_send_transaction_feature(self, wallet: WalletInfo, required_messages: int) -> None:
        feature = self._verify_feature_supported(wallet, "SendTransaction")
        max_messages = feature.get("maxMessages")

        if max_messages is not None:
            if max_messages < required_messages:
                logger.debug(
                    f"SendTransaction request exceeds wallet limit: "
                    f"max={max_messages}, required={required_messages}"
                )
                raise WalletNotSupportFeatureError(
                    f"Wallet cannot handle SendTransaction request: "
                    f"max supported messages {max_messages}, required {required_messages}."
                )
        else:
            logger.debug(
                "'maxMessages' not provided in SendTransaction feature. "
                "The request may be rejected by the wallet."
            )

    def get_max_supported_messages(self, wallet: WalletInfo) -> Optional[int]:
        """
        Retrieves the maximum number of supported messages for the 'SendTransaction' feature
        based on the connected wallet’s device features.

        :param wallet: WalletInfo object containing device capabilities.
        :return: The max number of messages or None if not specified.
        :raises TonConnectError: if wallet or feature information is invalid.
        """
        feature = self._verify_feature_supported(wallet, "SendTransaction")
        max_messages = feature.get("maxMessages")
        logger.debug(f"Max supported messages: {max_messages}")
        return max_messages
