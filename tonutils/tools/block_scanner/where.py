from __future__ import annotations

import typing as t

from tonutils.tools.block_scanner.annotations import TEvent


class Where(t.Generic[TEvent]):
    __slots__ = ()

    def __call__(self, event: TEvent) -> bool:
        raise NotImplementedError

    def __and__(self, other: Where[TEvent]) -> _And[TEvent]:
        return _And(self, other)

    def __or__(self, other: Where[TEvent]) -> _Or[TEvent]:
        return _Or(self, other)

    def __invert__(self) -> _Not[TEvent]:
        return _Not(self)


class _And(Where[TEvent]):
    __slots__ = ("_a", "_b")

    def __init__(self, a: Where[TEvent], b: Where[TEvent]) -> None:
        self._a = a
        self._b = b

    def __call__(self, event: TEvent) -> bool:
        return self._a(event) and self._b(event)


class _Or(Where[TEvent]):
    __slots__ = ("_a", "_b")

    def __init__(self, a: Where[TEvent], b: Where[TEvent]) -> None:
        self._a = a
        self._b = b

    def __call__(self, event: TEvent) -> bool:
        return self._a(event) or self._b(event)


class _Not(Where[TEvent]):
    __slots__ = ("_f",)

    def __init__(self, f: Where[TEvent]) -> None:
        self._f = f

    def __call__(self, event: TEvent) -> bool:
        return not self._f(event)
