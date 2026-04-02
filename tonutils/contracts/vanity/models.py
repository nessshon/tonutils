from __future__ import annotations

import base64
import json
import typing as t
from dataclasses import asdict, dataclass

from ton_core import Cell


@dataclass
class VanitySpecial:
    """Special contract flags for tick/tock execution."""

    tick: bool
    """Execute on tick transactions."""

    tock: bool
    """Execute on tock transactions."""


@dataclass
class VanityConfig:
    """Vanity address generation configuration."""

    owner: str
    """Owner address for the generated contract."""

    masterchain: bool
    """Generate masterchain address."""

    non_bounceable: bool
    """Use non-bounceable address format."""

    testnet: bool
    """Use testnet address format."""

    case_sensitive: bool
    """Case-sensitive prefix/suffix matching."""

    only_one: bool
    """Stop after first match."""

    start: str | None = None
    """Required address prefix, or ``None``."""

    end: str | None = None
    """Required address suffix, or ``None``."""


@dataclass
class VanityInit:
    """Vanity contract initialization parameters."""

    code: str
    """Base64url-encoded contract code BoC."""

    split_depth: int | None = None
    """Fixed prefix length for split depth, or ``None``."""

    special: VanitySpecial | None = None
    """Tick/tock flags, or ``None``."""

    @property
    def code_cell(self) -> Cell:
        """Decoded contract code as ``Cell``."""
        raw = base64.urlsafe_b64decode(self.code)
        return Cell.one_from_boc(raw)

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> VanityInit:
        """Create from dictionary."""
        special_raw = data.get("special")
        special = VanitySpecial(**special_raw) if isinstance(special_raw, dict) else special_raw
        return cls(
            code=data["code"],
            split_depth=data.get("fixedPrefixLength") or data.get("split_depth"),
            special=special,
        )


@dataclass
class VanityResult:
    """Result of a vanity address generation."""

    address: str
    """Generated address string."""

    init: VanityInit
    """Contract initialization parameters."""

    config: VanityConfig
    """Generation configuration used."""

    timestamp: float
    """Unix timestamp of the result."""

    def to_dict(self) -> dict[str, t.Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, t.Any]) -> VanityResult:
        """Create from dictionary."""
        init_raw = data.get("init", {})
        init = VanityInit.from_dict(init_raw) if isinstance(init_raw, dict) else init_raw
        config_raw = data.get("config", {})
        config = VanityConfig(**config_raw) if isinstance(config_raw, dict) else config_raw
        return cls(
            address=data["address"],
            init=init,
            config=config,
            timestamp=data["timestamp"],
        )

    @classmethod
    def from_json(cls, json_str: str) -> VanityResult:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))
