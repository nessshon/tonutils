import json
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

from pydantic import ValidationError

from tonutils.clients.adnl.provider.models import GlobalConfig


def load_global_config(source: str) -> GlobalConfig:
    try:
        if source.startswith(("http://", "https://")):
            with urllib.request.urlopen(source) as r:
                data = json.loads(r.read().decode("utf-8"))
        else:
            data = json.loads(Path(source).read_text(encoding="utf-8"))
        return GlobalConfig.model_validate(data)
    except HTTPError as e:
        raise RuntimeError(f"Config fetch failed: {e} ({source})") from e
    except URLError as e:
        raise RuntimeError(f"Config fetch failed: {e.reason} ({source})") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Config JSON is invalid: {e.msg} ({source})") from e
    except ValidationError as e:
        raise RuntimeError(f"Config validation failed: {e} ({source})") from e
    except OSError as e:
        raise RuntimeError(f"Config read failed: {e} ({source})") from e
    except Exception as e:
        raise RuntimeError(f"Config load failed: {e} ({source})") from e


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
