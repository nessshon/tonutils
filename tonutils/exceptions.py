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
    """Transport-level failure with structured context.

    Covers: TCP connect, ADNL handshake, send/recv, crypto failures.

    :param endpoint: Endpoint identifier (URL or "host:port").
    :param operation: What was attempted ("connect", "handshake", "send", "recv")
    :param reason: Why it failed ("timeout 2.0s", "connection refused", etc.)
    """

    endpoint: str
    operation: str
    reason: str

    def __init__(
        self,
        *,
        endpoint: str,
        operation: str,
        reason: str,
    ) -> None:
        self.endpoint = endpoint
        self.operation = operation
        self.reason = reason
        super().__init__(f"{operation} failed: {reason} ({endpoint})")


class ProviderError(TonutilsError):
    """Raise on provider-level failures (protocol, parsing, session/state)."""


class ClientError(TonutilsError):
    """Raise on client misuse, validation errors, or unsupported operations."""


class BalancerError(TonutilsError):
    """Raise on balancer failures (no alive backends, failover exhausted)."""


class NotConnectedError(TonutilsError, RuntimeError):
    """Raise when an operation requires an active connection."""

    component: str
    endpoint: t.Optional[str]
    operation: t.Optional[str]

    def __init__(
        self,
        *,
        component: str = "client",
        endpoint: t.Optional[str] = None,
        operation: t.Optional[str] = None,
        hint: t.Optional[str] = None,
    ) -> None:
        self.component = component
        self.endpoint = endpoint
        self.operation = operation

        if hint is None:
            hint = "Call connect() first or use an async context manager (`async with ...`)."

        where = f" ({endpoint})" if endpoint else ""
        prefix = f"cannot `{operation}`: " if operation else ""
        super().__init__(f"{prefix}{component} is not connected{where}. {hint}")


class ProviderTimeoutError(ProviderError, asyncio.TimeoutError):
    """Raise when a provider operation exceeds its timeout.

    :param timeout: Timeout in seconds.
    :param endpoint: Endpoint identifier (URL or host:port).
    :param operation: Operation label (e.g. "request", "connect").
    """

    timeout: float
    endpoint: str
    operation: str

    def __init__(self, *, timeout: float, endpoint: str, operation: str) -> None:
        self.timeout = timeout
        self.endpoint = endpoint
        self.operation = operation
        super().__init__(f"{operation} timed out after {timeout}s ({endpoint})")


class ProviderResponseError(ProviderError):
    """Raise when a backend returns an error response.

    :param code: Backend code (HTTP status or lite-server code).
    :param message: Backend error description.
    :param endpoint: Endpoint identifier (URL or host:port).
    """

    code: int
    message: str
    endpoint: str

    def __init__(self, *, code: int, message: str, endpoint: str) -> None:
        self.code = code
        self.message = message
        self.endpoint = endpoint
        super().__init__(f"request failed: {code} {message} ({endpoint})")


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
        self.attempts = attempts
        self.max_attempts = max_attempts
        self.last_error = last_error
        super().__init__(
            f"retry limit reached ({attempts}/{max_attempts}): {last_error}"
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
        super().__init__(f"{name} failed: {message}")


class StateNotLoadedError(ContractError):
    """Raise when a contract wrapper requires state that is not loaded.

    :param contract: Contract instance related to the failure.
    :param missing: Missing field name (e.g. "info", "state_data").
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
        self.exit_code = exit_code
        super().__init__(
            f"get-method `{method_name}` failed: exit code {exit_code} ({address})"
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
