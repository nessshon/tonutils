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
    """Base exception for all tonutils-specific errors."""

    @classmethod
    def _obj_name(cls, obj: t.Union[object, type, str]) -> str:
        """
        Resolve a human-readable class name from an object or type.

        :param obj: Instance, class or string name
        :return: Resolved name used in error messages
        """
        if isinstance(obj, type):
            return obj.__name__
        if isinstance(obj, str):
            return obj
        return obj.__class__.__name__


class ClientNotConnectedError(TonutilsException):
    """
    Raised when a client method is called without an active connection.

    This usually indicates that connect() or an async context manager
    was not used before making network requests.
    """

    def __init__(self, obj: t.Union[object, type, str]) -> None:
        name = self._obj_name(obj)
        super().__init__(
            f"`{name}` is not connected.\n"
            f"Use `async with {name}(...) as client:` "
            f"or call `await {name}(...).connect()` before making requests."
        )


class NotRefreshedError(TonutilsException):
    """
    Raised when accessing derived state before an explicit refresh.

    Typical usage is for contract wrappers that require refresh()
    to be called before accessing state_info or derived properties.
    """

    def __init__(self, obj: t.Union[object, type, str], attr: str) -> None:
        name = self._obj_name(obj)
        super().__init__(
            f"Access to `{attr}` is not allowed.\n"
            f"Call `await {name}.refresh()` before accessing `{attr}`."
        )


class ContractError(TonutilsException):
    """
    Generic error related to smart contract helpers.

    Used for configuration issues, invalid versions and similar
    contract wrapper problems.
    """

    def __init__(self, obj: t.Union[object, type, str], message: str) -> None:
        super().__init__(f"{self._obj_name(obj)}: {message}.")


class ClientError(TonutilsException):
    """
    Base error for client-side failures.

    Used for issues related to specific client implementations
    (HTTP, ADNL, balancers, etc.).
    """


class AdnlServerError(ClientError):
    """
    Lite-server reported an internal error while processing a request.

    Wraps lite-server error code and message as returned by ADNL.
    """

    def __init__(self, code: int, message: str) -> None:
        """
        :param code: Lite-server error code
        :param message: Lite-server error message
        """
        super().__init__(f"Lite-server crashed with `{code}` code. Message: {message}.")
        self.message = message
        self.code = code


class AdnlProviderError(ClientError):
    """
    Base error for ADNL provider failures.

    Includes additional context about the lite-server host and port.
    """

    def __init__(self, message: str, host: str, port: int) -> None:
        """
        :param message: Error description
        :param host: Lite-server host
        :param port: Lite-server port
        """
        full_message = f"{message} ({host}:{port})."
        super().__init__(full_message)
        self.host = host
        self.port = port


class AdnlProviderConnectError(AdnlProviderError):
    """
    Failed to establish an ADNL connection to the lite-server.

    Wraps network or handshake errors that occur during connect().
    """

    def __init__(self, host: str, port: int, message: str) -> None:
        super().__init__(
            f"Failed to connect: {message}.",
            host=host,
            port=port,
        )


class AdnlProviderClosedError(AdnlProviderError):
    """
    ADNL provider was closed while waiting for a response.

    Typically raised when transport is torn down during an in-flight
    request or when the remote peer closes connection unexpectedly.
    """

    def __init__(self, host: str, port: int) -> None:
        super().__init__(
            "Provider closed while waiting response.",
            host=host,
            port=port,
        )


class AdnlProviderResponseError(AdnlProviderError):
    """
    Received an invalid or malformed response from lite-server.

    Raised when the ADNL response payload does not match the expected
    structure or type.
    """

    def __init__(self, host: str, port: int) -> None:
        super().__init__(
            "Invalid response from provider.",
            host=host,
            port=port,
        )


class AdnlProviderMissingBlockError(AdnlProviderError):
    """
    Lite-server reported that a requested block is missing.

    Used for specific lite-server error codes that indicate
    absence of the requested block.
    """

    def __init__(self, attempts: int, host: str, port: int, message: str) -> None:
        super().__init__(
            f"Cannot load block after {attempts} attempts: {message}.",
            host=host,
            port=port,
        )
        self.attempts = attempts


class AdnlBalancerConnectionError(ClientError):
    """
    All ADNL lite-server providers failed to connect or process a request.

    Raised by AdnlBalancer when no healthy providers remain.
    """


class RateLimitExceededError(ClientError):
    """
    Request was retried multiple times but rate limits could not be bypassed.

    Raised after exhausting configured retry attempts.
    """

    def __init__(self, attempts: int) -> None:
        """
        :param attempts: Number of attempts performed before giving up
        """
        super().__init__(f"Rate limit exceeded after `{attempts}` attempts.")
        self.attempts = attempts


class RunGetMethodError(ClientError):
    """
    get-method execution failed with a non-zero exit code.

    Raised when lite-server returns exit_code != 0 for a runSmcMethod call.
    """

    def __init__(self, address: Address, method_name: str, exit_code: int) -> None:
        """
        :param address: Contract address on which get-method was executed
        :param method_name: Name of the get-method
        :param exit_code: Non-zero TVM exit code returned by the method
        """
        super().__init__(
            f"Get method `{method_name}` on `{address.to_str()}` "
            f"failed with `{exit_code}` exit code."
        )
        self.method_name = method_name
        self.exit_code = exit_code
        self.address = address


class AdnlTransportError(TonutilsException):
    """
    Base error for raw ADNL transport failures.

    Covers handshake, cipher initialization, framing and state issues.
    """


class AdnlHandshakeError(AdnlTransportError):
    """
    ADNL handshake failed during initial connection.

    Raised when the remote side closes the connection or does not
    respond within the expected timeout.
    """


class AdnlTransportStateError(AdnlTransportError):
    """
    Invalid internal state of the ADNL transport.

    Raised when required transport components (reader, writer, cipher, etc.)
    are not initialized or used incorrectly.
    """

    def __init__(self, message: str) -> None:
        super().__init__(f"ADNL transport state error: {message}.")


class AdnlTransportCipherError(AdnlTransportError):
    """
    ADNL cipher was used before being initialized.

    Raised when trying to encrypt or decrypt frames without
    a valid session cipher.
    """

    def __init__(self, direction: str) -> None:
        super().__init__(f"ADNL {direction} cipher is not initialized.")


class AdnlTransportFrameError(AdnlTransportError):
    """
    Malformed or invalid ADNL frame was received.

    Raised when frame length, structure or checksum validation fails.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid ADNL frame: {reason}.")
