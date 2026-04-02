from __future__ import annotations

import typing as t

from ton_core import GlobalConfig, load_global_config


def resolve_config(config: GlobalConfig | dict[str, t.Any] | str) -> GlobalConfig:
    """Normalize a config argument to ``GlobalConfig``.

    Accepts a ``GlobalConfig`` instance, a file path to a JSON config,
    or a raw dictionary and returns a ``GlobalConfig`` in all cases.

    :param config: ``GlobalConfig``, file path, or raw dict.
    :return: Resolved ``GlobalConfig`` instance.
    """
    if isinstance(config, str):
        config = load_global_config(config)
    if isinstance(config, dict):
        config = GlobalConfig.from_dict(config)
    return config
