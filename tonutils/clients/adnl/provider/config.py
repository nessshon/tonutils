from pydantic import ValidationError

from tonutils.clients.adnl.provider.models import GlobalConfig
from tonutils.utils import load_json


def load_global_config(source: str) -> GlobalConfig:
    """
    Fetch global configuration from source.

    :return: Parsed GlobalConfig instance
    """
    try:
        data = load_json(source)
        return GlobalConfig.model_validate(data)
    except ValidationError as e:
        raise RuntimeError(f"Config validation failed: {e} ({source})") from e


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
