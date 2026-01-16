import asyncio
import typing as t

__all__ = [
    "TonutilsError",
    "TransportError",
    "ProviderError",
    "ClientError",
    "ContractError",
    "BalancerError",
    "NotConnectedError",
    "ProviderTimeoutError",
    "ProviderResponseError",
    "RetryLimitError",
    "RunGetMethodError",
    "StateNotLoadedError",
    "CDN_CHALLENGE_MARKERS",
]


class TonutilsError(Exception):
    """Base exception for tonutils."""


class TransportError(TonutilsError):
    """Raise on transport-level failures (I/O, handshake, crypto, socket)."""


class ProviderError(TonutilsError):
    """Raise on provider-level failures (protocol, parsing, session/state)."""


class ClientError(TonutilsError):
    """Raise on client misuse, validation errors, or unsupported operations."""


class BalancerError(TonutilsError):
    """Raise on balancer failures (no alive backends, failover exhausted)."""


class NotConnectedError(TonutilsError, RuntimeError):
    """Raise when an operation requires an active connection.

    Typically means the underlying client/provider is not connected yet or was closed.
    """

    def __init__(self) -> None:
        super().__init__("not connected. Use `await connect()` or `async with ...`.")


class ProviderTimeoutError(ProviderError, asyncio.TimeoutError):
    """Raise when a provider operation exceeds its timeout.

    Used for both ADNL and HTTP providers.

    :param timeout: Timeout in seconds.
    :param endpoint: Endpoint identifier (URL or host:port).
    :param operation: Operation label (e.g. "adnl query", "http request").
    """

    timeout: float
    endpoint: str
    operation: str

    def __init__(self, *, timeout: float, endpoint: str, operation: str) -> None:
        self.timeout = float(timeout)
        self.endpoint = endpoint
        self.operation = operation
        super().__init__(f"{operation} timed out after {timeout}s: {endpoint}")


class ProviderResponseError(ProviderError):
    """Raise when a backend returns an error response.

    This is a normalized provider error for:
    - HTTP status codes (e.g. 429/5xx)
    - lite-server numeric error codes

    :param code: Backend code (HTTP status or lite-server code).
    :param message: Backend error description.
    :param endpoint: Endpoint identifier (URL or host:port).
    """

    code: int
    message: str
    endpoint: str

    def __init__(self, *, code: int, message: str, endpoint: str) -> None:
        self.code = int(code)
        self.message = message
        self.endpoint = endpoint
        super().__init__(f"request failed with code {code} at {endpoint}: {message}")


class RetryLimitError(ProviderError):
    """Raise when retry policy is exhausted for a matched rule.

    :param attempts: Attempts already performed for the matched rule.
    :param max_attempts: Maximum attempts allowed by the matched rule.
    :param last_error: Last provider error that triggered a retry.
    """

    attempts: int
    max_attempts: int
    last_error: ProviderError

    def __init__(
        self,
        *,
        attempts: int,
        max_attempts: int,
        last_error: ProviderError,
    ) -> None:
        self.attempts = int(attempts)
        self.max_attempts = int(max_attempts)
        self.last_error = last_error
        super().__init__(
            f"retry exhausted ({self.attempts}/{self.max_attempts}). "
            f"Last error: {last_error}"
        )


class ContractError(ClientError):
    """Raise when a contract wrapper operation fails.

    :param target: Contract instance or contract class related to the failure.
    :param message: Human-readable error message.
    """

    target: t.Any
    message: str

    def __init__(self, target: t.Any, message: str) -> None:
        self.target = target
        self.message = message

        name = (
            target.__name__ if isinstance(target, type) else target.__class__.__name__
        )
        super().__init__(f"{name}: {message}")


class StateNotLoadedError(ContractError):
    """Raise when a contract wrapper requires state that is not loaded.

    Typical cases:
    - state_info not fetched
    - state_data not decoded/available

    :param contract: Contract instance related to the failure.
    :param missing: Missing field name (e.g. "state_info", "state_data").
    """

    missing: str

    def __init__(self, contract: t.Any, *, missing: str) -> None:
        self.missing = missing
        name = contract.__class__.__name__
        super().__init__(contract, f"{missing} is not loaded. Call {name}.refresh().")


class RunGetMethodError(ClientError):
    """Raise when a contract get-method returns a non-zero TVM exit code.

    :param address: Contract address (string form).
    :param method_name: Get-method name.
    :param exit_code: TVM exit code.
    """

    address: str
    method_name: str
    exit_code: int

    def __init__(self, *, address: str, method_name: str, exit_code: int) -> None:
        self.address = address
        self.method_name = method_name
        self.exit_code = int(exit_code)
        super().__init__(
            f"get-method `{method_name}` failed for {address} (exit code {self.exit_code})."
        )


CDN_CHALLENGE_MARKERS: t.Dict[str, str] = {
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
"""Markers for detecting CDN / proxy challenge and anti-DDoS responses, 
used for error normalization and default retry policies."""
