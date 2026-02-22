import typing as t

from pydantic import (
    BaseModel as _BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
)
from pytoniq_core import Address, Cell, StateInit

from tonutils.types import Binary, NetworkGlobalID, PublicKey
from tonutils.utils import cell_to_b64, to_cell

__all__ = [
    "A",
    "BaseModel",
    "Binary64",
    "BocCell",
    "ChainId",
    "OptionalBinary64",
    "OptionalBocCell",
    "OptionalChainId",
    "OptionalTonAddress",
    "OptionalTonPublicKey",
    "OptionalWalletStateInit",
    "TonAddress",
    "TonPublicKey",
    "WalletStateInit",
]


T = t.TypeVar("T")
R = t.TypeVar("R")


class BaseModel(_BaseModel):
    """TonConnect base model with alias support and lenient parsing."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        arbitrary_types_allowed=True,
    )

    def dump(self, **kwargs: t.Any) -> t.Dict[str, t.Any]:
        """Dump to dict using alias keys."""
        return self.model_dump(by_alias=True, **kwargs)

    def dump_json(self, **kwargs: t.Any) -> str:
        """Dump to JSON string using alias keys."""
        return self.model_dump_json(by_alias=True, **kwargs)


# noinspection PyPep8Naming
def A(name: str, default: t.Any = ...) -> t.Any:
    """Create a Pydantic `Field` with matching validation and serialization alias.

    :param name: Alias name.
    :param default: Default value, or `...` for required.
    :return: Pydantic `Field`.
    """
    if default is ...:
        return Field(validation_alias=name, serialization_alias=name)
    return Field(default=default, validation_alias=name, serialization_alias=name)


def _conv_opt(conv: t.Callable[[t.Any], T]) -> t.Callable[[t.Any], t.Optional[T]]:
    """Wrap a converter to pass through `None`."""

    def _wrap(v: t.Any) -> t.Optional[T]:
        if v is None:
            return None
        return conv(v)

    return _wrap


def _ser_opt(ser: t.Callable[[T], R]) -> t.Callable[[t.Optional[T]], t.Optional[R]]:
    """Wrap a serializer to pass through `None`."""

    def _wrap(v: t.Optional[T]) -> t.Optional[R]:
        if v is None:
            return None
        return ser(v)

    return _wrap


def _as_address(v: t.Any) -> Address:
    return v if isinstance(v, Address) else Address(v)


def _as_network(v: t.Any) -> NetworkGlobalID:
    return v if isinstance(v, NetworkGlobalID) else NetworkGlobalID(int(v))


def _as_public_key(v: t.Any) -> PublicKey:
    return v if isinstance(v, PublicKey) else PublicKey(v)


def _as_state_init(v: t.Any) -> StateInit:
    if isinstance(v, StateInit):
        return v
    return StateInit.deserialize(to_cell(v).begin_parse())


def _as_cell(v: t.Any) -> Cell:
    return v if isinstance(v, Cell) else to_cell(v)


def _as_binary64(v: t.Any) -> Binary:
    return v if isinstance(v, Binary) else Binary(v, size=64)


def _s_address(v: Address) -> str:
    return v.to_str(is_user_friendly=False)


def _s_chain(v: NetworkGlobalID) -> str:
    return str(v.value)


def _s_pubkey(v: PublicKey) -> str:
    return v.as_hex


def _s_state_init(v: StateInit) -> str:
    return cell_to_b64(v.serialize())


def _s_cell(v: Cell) -> str:
    return cell_to_b64(v)


def _s_binary(v: Binary) -> str:
    return v.as_b64


TonAddress: t.TypeAlias = t.Annotated[
    Address,
    BeforeValidator(_as_address),
    PlainSerializer(_s_address, return_type=str),
]

OptionalTonAddress: t.TypeAlias = t.Annotated[
    t.Optional[Address],
    BeforeValidator(_conv_opt(_as_address)),
    PlainSerializer(_ser_opt(_s_address), return_type=t.Optional[str]),
]

ChainId: t.TypeAlias = t.Annotated[
    NetworkGlobalID,
    BeforeValidator(_as_network),
    PlainSerializer(_s_chain, return_type=str),
]

OptionalChainId: t.TypeAlias = t.Annotated[
    t.Optional[NetworkGlobalID],
    BeforeValidator(_conv_opt(_as_network)),
    PlainSerializer(_ser_opt(_s_chain), return_type=t.Optional[str]),
]

TonPublicKey: t.TypeAlias = t.Annotated[
    PublicKey,
    BeforeValidator(_as_public_key),
    PlainSerializer(_s_pubkey, return_type=str),
]

OptionalTonPublicKey: t.TypeAlias = t.Annotated[
    t.Optional[PublicKey],
    BeforeValidator(_conv_opt(_as_public_key)),
    PlainSerializer(_ser_opt(_s_pubkey), return_type=t.Optional[str]),
]

WalletStateInit: t.TypeAlias = t.Annotated[
    StateInit,
    BeforeValidator(_as_state_init),
    PlainSerializer(_s_state_init, return_type=str),
]

OptionalWalletStateInit: t.TypeAlias = t.Annotated[
    t.Optional[StateInit],
    BeforeValidator(_conv_opt(_as_state_init)),
    PlainSerializer(_ser_opt(_s_state_init), return_type=t.Optional[str]),
]

BocCell: t.TypeAlias = t.Annotated[
    Cell,
    BeforeValidator(_as_cell),
    PlainSerializer(_s_cell, return_type=str),
]

OptionalBocCell: t.TypeAlias = t.Annotated[
    t.Optional[Cell],
    BeforeValidator(_conv_opt(_as_cell)),
    PlainSerializer(_ser_opt(_s_cell), return_type=t.Optional[str]),
]

Binary64: t.TypeAlias = t.Annotated[
    Binary,
    BeforeValidator(_as_binary64),
    PlainSerializer(_s_binary, return_type=str),
]

OptionalBinary64: t.TypeAlias = t.Annotated[
    t.Optional[Binary],
    BeforeValidator(_conv_opt(_as_binary64)),
    PlainSerializer(_ser_opt(_s_binary), return_type=t.Optional[str]),
]
