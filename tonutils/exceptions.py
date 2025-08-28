import typing as t


class TonutilsException(Exception): ...


class ClientError(TonutilsException): ...


class KeyValidationError(TonutilsException): ...


class TextCipherError(TonutilsException): ...


class ContractError(TonutilsException):

    def __init__(
        self,
        obj: t.Union[object, type, str],
        message: str,
    ) -> None:
        if isinstance(obj, type):
            name = obj.__name__
        elif isinstance(obj, str):
            name = obj
        else:
            name = obj.__class__.__name__
        super().__init__(f"{name}: {message}")


class NotRefreshedError(TonutilsException):

    def __init__(
        self,
        obj: t.Union[object, type, str],
        attr: str,
    ) -> None:
        if isinstance(obj, type):
            name = obj.__name__
        elif isinstance(obj, str):
            name = obj
        else:
            name = obj.__class__.__name__
        super().__init__(
            f"Access to `{attr}` is not allowed. "
            f"Call `await {name}.refresh()` before accessing `{attr}`."
        )


class PytoniqDependencyError(TonutilsException):

    def __init__(self) -> None:
        super().__init__(
            "The `pytoniq` library is required to use `LiteserverClient` functionality. "
            "Please install it with `pip install pytonutils[pytoniq]`."
        )


class UnexpectedOpCodeError(TonutilsException):

    def __init__(
        self,
        obj: t.Union[object, type, str],
        expected: int,
        got: int,
    ) -> None:
        if isinstance(obj, type):
            name = obj.__name__
        elif isinstance(obj, str):
            name = obj
        else:
            name = obj.__class__.__name__
        ctx = f" while parsing {name}"
        super().__init__(
            f"Unexpected op code{ctx}: expected 0x{expected:08x}, "
            f"but received 0x{got:08x}."
        )


class UnsupportedStackItemError(TonutilsException):

    def __init__(self, item: t.Any) -> None:
        super().__init__(
            f"Unsupported item type for stack packing: got `{type(item).__name__}`."
        )


class UnsupportedStackSourceError(TonutilsException):

    def __init__(self, source: t.Any) -> None:
        super().__init__(f"Unsupported stack source: {source!r}.")
