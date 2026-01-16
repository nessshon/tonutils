import requests

from tonutils.clients.adnl.provider.models import GlobalConfig


def _get_global_config(path: str) -> GlobalConfig:
    url = f"https://ton.org/{path}"
    resp = requests.get(url)
    resp.raise_for_status()
    return GlobalConfig.model_validate(resp.json())


def get_mainnet_global_config() -> GlobalConfig:
    """
    Fetch mainnet global configuration.

    :return: Parsed GlobalConfig instance
    """
    return _get_global_config("global-config.json")


def get_testnet_global_config() -> GlobalConfig:
    """
    Fetch testnet global configuration.

    :return: Parsed GlobalConfig instance
    """
    return _get_global_config("testnet-global-config.json")
