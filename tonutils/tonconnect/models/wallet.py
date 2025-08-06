from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs, urlencode

from ..models import Account, DeviceInfo, TonProof
from ..utils.exceptions import TonConnectError


@dataclass
class WalletApp:
    """
    Represents a wallet application with relevant metadata and URLs.
    """
    app_name: str
    name: str
    image: Optional[str] = None
    bridge_url: Optional[str] = None
    tondns: Optional[str] = None
    about_url: Optional[str] = None
    universal_url: Optional[str] = None
    deep_link: Optional[str] = None
    platforms: Optional[List[str]] = None

    def __repr__(self) -> str:
        return (
            f"WalletApp(app_name={self.app_name}, "
            f"name={self.name}, "
            f"image={self.image}, "
            f"bridge_url={self.bridge_url}, "
            f"tondns={self.tondns}, "
            f"about_url={self.about_url}, "
            f"universal_url={self.universal_url}, "
            f"deep_link={self.deep_link}, "
            f"platforms={self.platforms})"
        )

    @property
    def direct_url(self) -> Optional[str]:
        """
        Converts the universal URL to a direct URL by modifying query parameters.

        :return: The direct URL as a string.
        """
        if self.universal_url is None:
            return None

        url = self.universal_url_to_direct_url(self.universal_url)
        return url + "?startapp=tonconnect" if "t.me/wallet" in url else url

    @staticmethod
    def universal_url_to_direct_url(universal_url: str) -> str:
        """
        Transforms a universal URL into a direct URL by adjusting its path and query parameters.

        :param universal_url: The universal URL to convert.
        :return: The converted direct URL.
        """
        parsed = urlparse(universal_url)
        query_dict = parse_qs(parsed.query)

        # Remove the 'attach' parameter if present and modify the path
        if query_dict.pop("attach", None) is not None:
            new_path = parsed.path.rstrip("/")
            if not new_path.endswith("/start"):
                new_path += "/start"
            parsed = parsed._replace(path=new_path)

        # Reconstruct the query string without the removed parameters
        new_query = urlencode(query_dict, doseq=True)
        parsed = parsed._replace(query=new_query)
        return parsed.geturl()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WalletApp:
        """
        Creates a WalletApp instance from a dictionary containing wallet data.

        :param data: A dictionary with wallet information.
        :return: An instance of WalletApp.
        """
        return cls(
            app_name=data.get("app_name"),  # type: ignore
            name=data.get("name"),  # type: ignore
            image=data.get("image"),
            bridge_url=data.get("bridge_url"),
            tondns=data.get("tondns"),
            about_url=data.get("about_url"),
            universal_url=data.get("universal_url"),
            deep_link=data.get("deepLink"),
            platforms=data.get("platforms"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the WalletApp instance into a dictionary format suitable for serialization.

        :return: A dictionary representation of the WalletApp.
        """
        return {
            "app_name": self.app_name,
            "name": self.name,
            "image": self.image,
            "bridge_url": self.bridge_url,
            "tondns": self.tondns,
            "about_url": self.about_url,
            "universal_url": self.universal_url,
            "deepLink": self.deep_link,
            "platforms": self.platforms,
        }


@dataclass
class WalletInfo:
    """
    Represents detailed information about a connected wallet, including device info,
    account details, provider, and TON proof.
    """

    device: Optional[DeviceInfo] = None
    provider: str = field(default="http")
    account: Optional[Account] = None
    ton_proof: Optional[TonProof] = None

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> WalletInfo:
        """
        Creates a WalletInfo instance from a payload dictionary.

        :param payload: A dictionary containing wallet payload data.
        :raises TonConnectError: If required items are missing in the payload.
        :return: An instance of WalletInfo.
        """
        items = payload.get("items")
        if not items:
            raise TonConnectError("items not contains in payload")

        wallet = cls()
        public_key: Optional[bytes] = None

        for item in items:
            if item.get("name") == "ton_addr":
                wallet.account = Account.from_dict(item)
                public_key = wallet.account.public_key

        for item in items:
            if item.get("name") == "ton_proof":
                item["public_key"] = public_key.hex()
                wallet.ton_proof = TonProof.from_dict(item)

        if not wallet.account:
            raise TonConnectError("ton_addr not contains in items")

        device_info = payload.get("device")
        if device_info:
            wallet.device = DeviceInfo.from_dict(device_info)

        return wallet

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WalletInfo:
        """
        Creates a WalletInfo instance from a dictionary containing wallet data.

        :param data: A dictionary with wallet information.
        :return: An instance of WalletInfo.
        """
        device_data = data.get("device")
        account_data = data.get("account")
        ton_proof_data = data.get("ton_proof")

        device_obj = None
        if device_data is not None:
            device_obj = DeviceInfo.from_dict(device_data)

        account_obj = None
        if account_data is not None:
            account_obj = Account.from_dict(account_data)

        ton_proof_obj = None
        if ton_proof_data is not None:
            ton_proof_obj = TonProof.from_dict(ton_proof_data)

        return cls(
            device=device_obj,
            provider=data.get("provider", "http"),
            account=account_obj,
            ton_proof=ton_proof_obj,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the WalletInfo instance into a dictionary format suitable for serialization.

        :return: A dictionary representation of the WalletInfo.
        """
        return {
            "device": self.device.to_dict() if self.device else None,
            "provider": self.provider,
            "account": self.account.to_dict() if self.account else None,
            "ton_proof": self.ton_proof.to_dict() if self.ton_proof else None,
        }
