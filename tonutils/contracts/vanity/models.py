from __future__ import annotations

import base64
import json
import typing as t
from dataclasses import dataclass, asdict

from pytoniq_core import Cell


@dataclass
class VanitySpecial:
    """Special contract flags for tick/tock execution.

    Attributes:
        tick: Execute on tick transactions.
        tock: Execute on tock transactions.
    """

    tick: bool
    tock: bool


@dataclass
class VanityConfig:
    """Vanity address generation configuration.

    Attributes:
        owner: Owner address for the generated contract.
        start: Required address prefix, or `None`.
        end: Required address suffix, or `None`.
        masterchain: Generate masterchain address.
        non_bounceable: Use non-bounceable address format.
        testnet: Use testnet address format.
        case_sensitive: Case-sensitive prefix/suffix matching.
        only_one: Stop after first match.
    """

    owner: str
    masterchain: bool
    non_bounceable: bool
    testnet: bool
    case_sensitive: bool
    only_one: bool
    start: t.Optional[str] = None
    end: t.Optional[str] = None


@dataclass
class VanityInit:
    """Vanity contract initialization parameters.

    Attributes:
        code: Base64url-encoded contract code BoC.
        split_depth: Fixed prefix length for split depth, or `None`.
        special: Tick/tock flags, or `None`.
    """

    code: str
    split_depth: t.Optional[int] = None
    special: t.Optional[VanitySpecial] = None

    @property
    def code_cell(self) -> Cell:
        """Decoded contract code as ``Cell``."""
        raw = base64.urlsafe_b64decode(self.code)
        return Cell.one_from_boc(raw)

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> VanityInit:
        special_raw = data.get("special")
        special = VanitySpecial(**special_raw) if isinstance(special_raw, dict) else special_raw
        return cls(
            code=data["code"],
            split_depth=data.get("fixedPrefixLength") or data.get("split_depth"),
            special=special,
        )


@dataclass
class VanityResult:
    """Result of a vanity address generation.

    Attributes:
        address: Generated address string.
        init: Contract initialization parameters.
        config: Generation configuration used.
        timestamp: Unix timestamp of the result.
    """

    address: str
    init: VanityInit
    config: VanityConfig
    timestamp: float

    def to_dict(self) -> t.Dict[str, t.Any]:
        """Serialize to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: t.Dict[str, t.Any]) -> VanityResult:
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
        return cls.from_dict(json.loads(json_str))
