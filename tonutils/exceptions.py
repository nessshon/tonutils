from __future__ import annotations

import asyncio
import typing as t

__all__ = [
    "CDN_CHALLENGE_MARKERS",
    "TVM_EXIT_CODES",
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

    def __init__(self, *args: t.Any, hint: str | None = None) -> None:
        """Initialize the error.

        :param hint: Actionable suggestion for the developer.
        """
        super().__init__(*args)
        self.hint = hint

    def __str__(self) -> str:
        """Return message with hint appended if present."""
        msg = super().__str__()
        if self.hint:
            return f"{msg}\n  Hint: {self.hint}"
        return msg


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
        super().__init__(
            f"{op}{component} is not connected{where}",
            hint="Use `async with` context manager or call `.connect()` first.",
        )


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
        super().__init__(
            f"retry limit reached {ratio}: {last_error}",
            hint="Adjust RetryPolicy limits or check endpoint availability.",
        )


class NetworkNotSupportedError(ClientError, KeyError):
    """No built-in defaults for the given network in a provider."""

    def __init__(self, network: t.Any, *, provider: str) -> None:
        """Initialize the network-not-supported error.

        :param network: The network identifier.
        :param provider: Provider or client name.
        """
        self.network = network
        self.provider = provider
        super().__init__(f"No default for network {network!r} in {provider}. Provide connection details explicitly.")


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

    def __init__(self, target: t.Any, details: str, *, hint: str | None = None) -> None:
        """Initialize the contract error.

        :param target: Contract class or instance that failed.
        :param details: Failure description.
        :param hint: Actionable suggestion for the developer.
        """
        self.target = target
        self.details = details

        name = target.__name__ if isinstance(target, type) else target.__class__.__name__
        super().__init__(f"{name} failed: {details}", hint=hint)


class StateNotLoadedError(ContractError):
    """Contract wrapper requires state that is not loaded."""

    def __init__(self, contract: t.Any, *, missing: str) -> None:
        """Initialize the state-not-loaded error.

        :param contract: Contract instance missing the state.
        :param missing: Name of the missing state attribute.
        """
        self.missing = missing
        name = contract.__class__.__name__
        super().__init__(
            contract,
            f"{missing} is not loaded. Call {name}.refresh().",
            hint="Load on-chain state first: `await contract.refresh()`.",
        )


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

        reason = TVM_EXIT_CODES.get(self.exit_code, "unknown error")
        super().__init__(
            f"get-method `{method_name}` failed: exit code {self.exit_code} — {reason} ({address})",
            hint=_tvm_hint(self.exit_code, method_name),
        )


def _tvm_hint(exit_code: int, method_name: str) -> str | None:
    """Return an actionable hint for the given TVM exit code.

    :param exit_code: TVM exit code.
    :param method_name: Name of the get-method that failed.
    :return: Hint string, or ``None`` if no hint is available.
    """
    hints: dict[int, str] = {
        2: "Check the arguments passed to `run_get_method` stack.",
        4: "Input value is too large or division by zero occurred.",
        5: "An argument is out of its expected range; check input values.",
        7: "Stack arguments have wrong types; check `run_get_method` stack format.",
        8: "Result cell exceeds 1023 bits or 4 refs; contract may need a redesign.",
        9: "Input data is shorter than the contract expects; check BoC encoding.",
        11: (
            f"Method `{method_name}` may not exist on this contract. "
            "Verify the contract is deployed and supports this method."
        ),
        13: "Contract ran out of gas. Increase gas limit or simplify the query.",
        -14: "Contract ran out of gas. Increase gas limit or simplify the query.",
    }
    return hints.get(exit_code)


TVM_EXIT_CODES: dict[int, str] = {
    0: "success",
    1: "alternative success",
    2: "stack underflow",
    3: "stack overflow",
    4: "integer overflow or division by zero",
    5: "integer out of expected range",
    6: "invalid opcode",
    7: "type check error",
    8: "cell overflow (>1023 bits or >4 refs)",
    9: "cell underflow (not enough data in slice)",
    10: "dictionary error",
    11: "unknown error (often: method not found)",
    12: "fatal error",
    13: "out of gas",
    -14: "out of gas (negated)",
    14: "virtualization error (reserved, never thrown)",
    32: "invalid action list",
    33: "action list too long (>255 actions)",
    34: "invalid or unsupported action",
    35: "invalid source address in outbound message",
    36: "invalid destination address",
    37: "not enough TON for action/forward fees",
    38: "not enough extra currencies",
    39: "outbound message does not fit into a cell",
    40: "cannot process message (insufficient funds or too large)",
    41: "library reference is null",
    42: "library change action error",
    43: "library limits exceeded (max cells or Merkle depth)",
    50: "account state size exceeded limits",
}
"""Mapping of standard TVM exit codes to human-readable descriptions."""

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
