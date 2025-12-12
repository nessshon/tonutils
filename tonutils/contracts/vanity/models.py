import base64
import typing as t

from pydantic import BaseModel, Field
from pytoniq_core import Cell


class VanitySpecial(BaseModel):
    tick: bool
    tock: bool


class VanityConfig(BaseModel):
    owner: str
    start: t.Optional[str] = None
    end: t.Optional[str] = None
    masterchain: bool
    non_bounceable: bool
    testnet: bool
    case_sensitive: bool
    only_one: bool


class VanityInit(BaseModel):
    code: str
    split_depth: t.Optional[int] = Field(default=None, alias="fixedPrefixLength")
    special: t.Optional[VanitySpecial] = None

    @property
    def code_cell(self) -> Cell:
        raw = base64.urlsafe_b64decode(self.code)
        return Cell.one_from_boc(raw)


class VanityResult(BaseModel):
    address: str
    init: VanityInit
    config: VanityConfig
    timestamp: float
