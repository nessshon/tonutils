from __future__ import annotations

import typing as t

from pytoniq_core import Address

from tonutils.tools.block_scanner import TransactionEvent
from tonutils.tools.block_scanner.annotations import TEvent
from tonutils.types import AddressLike


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


class _Opcode(Where[TransactionEvent]):
    __slots__ = ("_ops",)

    def __init__(self, *ops: int) -> None:
        self._ops = frozenset(ops)

    def __call__(self, event: TransactionEvent) -> bool:
        msg = event.transaction.in_msg
        if msg is None or msg.body is None:
            return False

        if len(msg.body.bits) < 32:
            return False

        op = msg.body.begin_parse().load_uint(32)
        return op in self._ops


class _Comment(Where[TransactionEvent]):
    __slots__ = ("_texts", "_any")

    def __init__(self, *texts: str) -> None:
        self._texts = frozenset(texts)
        self._any = len(texts) == 0

    def __call__(self, event: TransactionEvent) -> bool:
        msg = event.transaction.in_msg
        if msg is None or msg.body is None:
            return False

        body = msg.body.begin_parse()
        if len(body.bits) < 32:
            return False

        op = body.load_uint(32)
        if op != 0:
            return False

        if self._any:
            return True
        try:
            text = body.load_snake_string()
        except (Exception,):
            return False

        return text in self._texts


class _Sender(Where[TransactionEvent]):
    __slots__ = ("_addrs",)

    def __init__(self, *addrs: AddressLike) -> None:
        self._addrs = frozenset(Address(a) if isinstance(a, str) else a for a in addrs)

    def __call__(self, event: TransactionEvent) -> bool:
        msg = event.transaction.in_msg
        if msg is None:
            return False

        src = msg.info.src
        return src is not None and src in self._addrs


class _Destination(Where[TransactionEvent]):
    __slots__ = ("_addrs",)

    def __init__(self, *addrs: AddressLike) -> None:
        self._addrs = frozenset(Address(a) if isinstance(a, str) else a for a in addrs)

    def __call__(self, event: TransactionEvent) -> bool:
        msg = event.transaction.in_msg
        if msg is None:
            return False

        dest = msg.info.dest
        return dest is not None and dest in self._addrs


def opcode(*ops: int) -> Where[TransactionEvent]:
    return _Opcode(*ops)


def comment(*texts: str) -> Where[TransactionEvent]:
    return _Comment(*texts)


def sender(*addresses: AddressLike) -> Where[TransactionEvent]:
    return _Sender(*addresses)


def destination(*addresses: AddressLike) -> Where[TransactionEvent]:
    return _Destination(*addresses)
