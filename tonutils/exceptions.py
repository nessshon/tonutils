import typing as t

from pytoniq_core import Address

__all__ = [
    "TonutilsException",
    "ClientNotConnectedError",
    "NotRefreshedError",
    "ContractError",
    "ClientError",
    "AdnlServerError",
    "AdnlProviderError",
    "AdnlProviderConnectError",
    "AdnlProviderClosedError",
    "AdnlProviderResponseError",
    "AdnlProviderMissingBlockError",
    "AdnlBalancerConnectionError",
    "RateLimitExceededError",
    "RunGetMethodError",
    "AdnlHandshakeError",
    "AdnlTransportError",
    "AdnlTransportStateError",
    "AdnlTransportCipherError",
    "AdnlTransportFrameError",
]


class TonutilsException(Exception):
    @classmethod
    def _obj_name(cls, obj: t.Union[object, type, str]) -> str:
        if isinstance(obj, type):
            return obj.__name__
        if isinstance(obj, str):
            return obj
        return obj.__class__.__name__


class ClientNotConnectedError(TonutilsException):
    def __init__(self, obj: t.Union[object, type, str]) -> None:
        name = self._obj_name(obj)
        super().__init__(
            f"`{name}` is not connected.\n"
            f"Use `async with {name}(...) as client:` "
            f"or call `await {name}(...).connect()` before making requests."
        )


class NotRefreshedError(TonutilsException):
    def __init__(self, obj: t.Union[object, type, str], attr: str) -> None:
        name = self._obj_name(obj)
        super().__init__(
            f"Access to `{attr}` is not allowed.\n"
            f"Call `await {name}.refresh()` before accessing `{attr}`."
        )


class ContractError(TonutilsException):
    def __init__(self, obj: t.Union[object, type, str], message: str) -> None:
        super().__init__(f"{self._obj_name(obj)}: {message}.")


class ClientError(TonutilsException): ...


class AdnlServerError(ClientError):

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"Lite-server crashed with `{code}` code. Message: {message}.")
        self.message = message
        self.code = code


class AdnlProviderError(ClientError):
    def __init__(self, message: str, host: str, port: int) -> None:
        full_message = f"{message} ({host}:{port})."
        super().__init__(full_message)
        self.host = host
        self.port = port


class AdnlProviderConnectError(AdnlProviderError):
    def __init__(self, host: str, port: int, message: str) -> None:
        super().__init__(
            f"Failed to connect: {message}.",
            host=host,
            port=port,
        )


class AdnlProviderClosedError(AdnlProviderError):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(
            "Provider closed while waiting response.",
            host=host,
            port=port,
        )


class AdnlProviderResponseError(AdnlProviderError):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(
            "Invalid response from provider.",
            host=host,
            port=port,
        )


class AdnlProviderMissingBlockError(AdnlProviderError):
    def __init__(self, host: str, port: int, message: str) -> None:
        super().__init__(
            f"Block not found: {message}.",
            host=host,
            port=port,
        )


class AdnlBalancerConnectionError(ClientError): ...


class RateLimitExceededError(ClientError):
    def __init__(self, attempts: int) -> None:
        super().__init__(f"Rate limit exceeded after `{attempts}` attempts.")
        self.attempts = attempts


class RunGetMethodError(ClientError):
    def __init__(self, address: Address, method_name: str, exit_code: int) -> None:
        super().__init__(
            f"Get method `{method_name}` on `{address.to_str()}` "
            f"failed with `{exit_code}` exit code."
        )
        self.method_name = method_name
        self.exit_code = exit_code
        self.address = address


class AdnlTransportError(TonutilsException): ...


class AdnlHandshakeError(AdnlTransportError): ...


class AdnlTransportStateError(AdnlTransportError):
    def __init__(self, message: str) -> None:
        super().__init__(f"ADNL transport state error: {message}.")


class AdnlTransportCipherError(AdnlTransportError):
    def __init__(self, direction: str) -> None:
        super().__init__(f"ADNL {direction} cipher is not initialized.")


class AdnlTransportFrameError(AdnlTransportError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid ADNL frame: {reason}.")
