import base64
import typing as t

from pydantic import BaseModel, Field
from pytoniq_core import Cell


class VanitySpecial(BaseModel):
    """Special contract flags for tick/tock execution.

    Attributes:
        tick: Execute on tick transactions.
        tock: Execute on tock transactions.
    """

    tick: bool
    tock: bool


class VanityConfig(BaseModel):
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
    start: t.Optional[str] = None
    end: t.Optional[str] = None
    masterchain: bool
    non_bounceable: bool
    testnet: bool
    case_sensitive: bool
    only_one: bool


class VanityInit(BaseModel):
    """Vanity contract initialization parameters.

    Attributes:
        code: Base64url-encoded contract code BoC.
        split_depth: Fixed prefix length for split depth, or `None`.
        special: Tick/tock flags, or `None`.
    """

    code: str
    split_depth: t.Optional[int] = Field(default=None, alias="fixedPrefixLength")
    special: t.Optional[VanitySpecial] = None

    @property
    def code_cell(self) -> Cell:
        """Decoded contract code as `Cell`."""
        raw = base64.urlsafe_b64decode(self.code)
        return Cell.one_from_boc(raw)


class VanityResult(BaseModel):
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
