import decimal
import typing as t

from ..types.common import NumberLike

_MIN_VAL = 0
_MAX_VAL = 2**256 - 1
_ROUND_DOWN = decimal.ROUND_DOWN


def _dynamic_prec(decimals: int) -> int:
    return len(str(_MAX_VAL)) + decimals + 10


def _to_decimal(x: NumberLike) -> decimal.Decimal:
    if isinstance(x, decimal.Decimal):
        return x
    if isinstance(x, float):
        return decimal.Decimal(str(x))
    return decimal.Decimal(x)


def to_nano(value: NumberLike, decimals: int = 9) -> int:
    if decimals < 0:
        raise ValueError("decimals must be >= 0")

    d = _to_decimal(value)
    factor = decimal.Decimal(10) ** decimals

    with decimal.localcontext() as ctx:
        ctx.prec = _dynamic_prec(decimals)
        result = (d * factor).quantize(decimal.Decimal(1), rounding=_ROUND_DOWN)

    if not (_MIN_VAL <= result <= _MAX_VAL):
        raise ValueError("Resulting value must be between 0 and 2**256 - 1")

    return int(result)


def to_amount(
    value: int,
    decimals: int = 9,
    *,
    precision: t.Optional[int] = None,
) -> decimal.Decimal:
    if decimals < 0:
        raise ValueError("decimals must be >= 0")
    if not (_MIN_VAL <= value <= _MAX_VAL):
        raise ValueError("Value must be between 0 and 2**256 - 1")

    if value == 0:
        return decimal.Decimal(0)

    with decimal.localcontext() as ctx:
        ctx.prec = _dynamic_prec(decimals)
        result = decimal.Decimal(value) / (decimal.Decimal(10) ** decimals)

    if precision is not None:
        quant = decimal.Decimal(1) / (decimal.Decimal(10) ** precision)
        result = result.quantize(quant, rounding=_ROUND_DOWN)

    return result
