from pydantic import ValidationError

from tonutils.clients.adnl.provider.models import GlobalConfig
from tonutils.utils import load_json

MAINNET_GLOBAL_CONFIG_URL = "https://ton.org/global-config.json"
TESTNET_GLOBAL_CONFIG_URL = "https://ton.org/testnet-global-config.json"


def load_global_config(source: str) -> GlobalConfig:
    """Load and validate a TON global configuration from URL or file path.

    :param source: URL or local file path to the JSON config.
    :return: Parsed `GlobalConfig` instance.
    :raises RuntimeError: If validation fails.
    """
    try:
        data = load_json(source)
        return GlobalConfig.model_validate(data)
    except ValidationError as e:
        raise RuntimeError(f"Config validation failed: {e} ({source})") from e


def get_mainnet_global_config() -> GlobalConfig:
    """Fetch mainnet global configuration from ton.org.

    :return: Parsed `GlobalConfig` instance.
    """
    return load_global_config(MAINNET_GLOBAL_CONFIG_URL)


def get_testnet_global_config() -> GlobalConfig:
    """Fetch testnet global configuration from ton.org.

    :return: Parsed `GlobalConfig` instance.
    """
    return load_global_config(TESTNET_GLOBAL_CONFIG_URL)
