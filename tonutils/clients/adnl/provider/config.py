import json
import urllib.request
from pathlib import Path

from tonutils.clients.adnl.provider.models import GlobalConfig


def load_global_config(source: str) -> GlobalConfig:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as response:
            data = json.loads(response.read().decode())
    else:
        data = json.loads(Path(source).read_text())

    return GlobalConfig.model_validate(data)


def get_mainnet_global_config() -> GlobalConfig:
    """
    Fetch mainnet global configuration.

    :return: Parsed GlobalConfig instance
    """
    return load_global_config("https://ton.org/global-config.json")


def get_testnet_global_config() -> GlobalConfig:
    """
    Fetch testnet global configuration.

    :return: Parsed GlobalConfig instance
    """
    return load_global_config("https://ton.org/testnet-global-config.json")
