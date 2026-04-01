import asyncio
import typing as t

__all__ = [
    "CDN_CHALLENGE_MARKERS",
    "BalancerError",
    "ClientError",
    "ContractError",
    "DhtValueNotFoundError",
    "NetworkNotSupportedError",
    "NotConnectedError",
    "ProviderError",
    "ProviderResponseError",
    "ProviderTimeoutError",
    "RetryLimitError",
    "RunGetMethodError",
    "StateNotLoadedError",
    "TonutilsError",
    "TransportError",
]


class TonutilsError(Exception):
    """Base exception for tonutils."""


class TransportError(TonutilsError):
    """Transport-level failure (connect/handshake/send/recv)."""

    def __init__(self, *, endpoint: str, operation: str, reason: str) -> None:
        """Initialize the transport error.

        :param endpoint: Remote endpoint identifier.
        :param operation: Failed operation name.
        :param reason: Failure description.
        """
        self.endpoint = endpoint
        self.operation = operation
        self.reason = reason
        super().__init__(f"{operation} failed: {reason} ({endpoint})")


class ProviderError(TonutilsError):
    """Provider-level failure (protocol/parsing/backend/state)."""


class ClientError(TonutilsError):
    """Client misuse, validation errors, or unsupported operations."""


class BalancerError(TonutilsError):
    """Balancer failure (no alive backends, failover exhausted)."""


class NotConnectedError(TonutilsError, RuntimeError):
    """Raised when an operation requires an active connection."""

    def __init__(
        self,
        *,
        component: str = "client",
        endpoint: str | None = None,
        operation: str | None = None,
    ) -> None:
        """Initialize the not-connected error.

        :param component: Name of the disconnected component.
        :param endpoint: Remote endpoint identifier.
        :param operation: Operation that required a connection.
        """
        self.component = component
        self.endpoint = endpoint
        self.operation = operation

        op = f"cannot `{operation}`: " if operation else ""
        where = f" ({endpoint})" if endpoint else ""
        super().__init__(f"{op}{component} is not connected{where}")


class ProviderTimeoutError(ProviderError, asyncio.TimeoutError):
    """Provider operation exceeded its timeout."""

    def __init__(self, *, timeout: float, endpoint: str, operation: str) -> None:
        """Initialize the timeout error.

        :param timeout: Timeout threshold in seconds.
        :param endpoint: Remote endpoint identifier.
        :param operation: Operation that timed out.
        """
        self.timeout = float(timeout)
        self.endpoint = endpoint
        self.operation = operation
        super().__init__(f"{operation} timed out after {self.timeout}s ({endpoint})")


class ProviderResponseError(ProviderError):
    """Backend returned an error response."""

    def __init__(self, *, code: int, message: str, endpoint: str) -> None:
        """Initialize the response error.

        :param code: Error code from the backend.
        :param message: Error message from the backend.
        :param endpoint: Remote endpoint identifier.
        """
        self.code = int(code)
        self.message = message
        self.endpoint = endpoint
        super().__init__(f"request failed: {self.code} {self.message} ({endpoint})")


class RetryLimitError(ProviderError):
    """Retry policy exhausted."""

    def __init__(
        self,
        attempts: int,
        max_attempts: int,
        last_error: ProviderError,
    ) -> None:
        """Initialize the retry limit error.

        :param attempts: Number of attempts performed.
        :param max_attempts: Maximum attempts allowed by the policy.
        :param last_error: Last error before giving up.
        """
        self.attempts = int(attempts)
        self.max_attempts = int(max_attempts)
        self.last_error = last_error
        ratio = f"{self.attempts}/{self.max_attempts}"
        super().__init__(f"retry limit reached {ratio}: {last_error}")


class NetworkNotSupportedError(ClientError, KeyError):
    """No built-in defaults for the given network in a provider."""

    def __init__(self, network: t.Any, *, provider: str) -> None:
        """Initialize the network-not-supported error.

        :param network: The network identifier.
        :param provider: Provider or client name.
        """
        self.network = network
        self.provider = provider
        super().__init__(
            f"No default for network {network!r} in {provider}. "
            "Provide connection details explicitly."
        )


class DhtValueNotFoundError(ClientError):
    """DHT value not found for the requested key."""

    def __init__(self, *, key: bytes) -> None:
        """Initialize the DHT value-not-found error.

        :param key: 256-bit key that was not found.
        """
        self.key = key
        super().__init__(f"DHT value not found for key {key.hex()}")


class ContractError(ClientError):
    """Contract wrapper operation failed."""

    def __init__(self, target: t.Any, details: str) -> None:
        """Initialize the contract error.

        :param target: Contract class or instance that failed.
        :param details: Failure description.
        """
        self.target = target
        self.details = details

        name = target.__name__ if isinstance(target, type) else target.__class__.__name__
        super().__init__(f"{name} failed: {details}")


class StateNotLoadedError(ContractError):
    """Contract wrapper requires state that is not loaded."""

    def __init__(self, contract: t.Any, *, missing: str) -> None:
        """Initialize the state-not-loaded error.

        :param contract: Contract instance missing the state.
        :param missing: Name of the missing state attribute.
        """
        self.missing = missing
        name = contract.__class__.__name__
        super().__init__(contract, f"{missing} is not loaded. Call {name}.refresh().")


class RunGetMethodError(ClientError):
    """Contract get-method returned a non-zero TVM exit code."""

    def __init__(self, *, address: str, exit_code: int, method_name: str) -> None:
        """Initialize the get-method error.

        :param address: Contract address.
        :param exit_code: TVM exit code returned by the method.
        :param method_name: Name of the get-method that failed.
        """
        self.address = address
        self.exit_code = int(exit_code)
        self.method_name = method_name
        super().__init__(
            f"get-method `{method_name}` failed: exit code {self.exit_code} ({address})"
        )


CDN_CHALLENGE_MARKERS: dict[str, str] = {
    # Cloudflare
    "cloudflare": "Cloudflare protection triggered or blocked the request.",
    "cf-ray": "Cloudflare intermediate error (cf-ray header detected).",
    "just a moment": "Cloudflare browser verification page.",
    "checking your browser": "Cloudflare browser verification page.",
    "attention required": "Cloudflare challenge page.",
    "captcha": "Cloudflare CAPTCHA challenge.",
    # Other CDNs / proxies
    "akamai": "Akamai CDN blocked or intercepted the request.",
    "fastly": "Fastly CDN error response detected.",
    "varnish": "Varnish cache/CDN interference.",
    "nginx": "Reverse proxy (nginx) error response.",
    # Upstream failures
    "502 bad gateway": "Bad gateway from upstream or proxy.",
    "503 service unavailable": "Service temporarily unavailable (proxy or CDN).",
    "ddos": "Possible DDoS protection or mitigation page.",
}
"""Mapping of CDN challenge markers to human-readable error messages."""
