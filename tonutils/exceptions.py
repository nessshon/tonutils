class TonutilsException(Exception):
    pass


class APIClientError(TonutilsException):
    """Base class for all API client errors."""
    pass


class RateLimitExceeded(APIClientError):
    """Raised when the request fails due to exceeding rate limits."""

    def __init__(self, url: str, attempts: int):
        super().__init__(f"Request to {url} failed after {attempts} attempts due to rate limiting (HTTP 429).")


class UnauthorizedError(APIClientError):
    """Raised when unauthorized (401)."""

    def __init__(self, url: str):
        super().__init__(f"Unauthorized (HTTP 401). Check your API key or permissions for {url}.")


class HTTPClientResponseError(APIClientError):
    """Raised when a non-OK HTTP response is received."""

    def __init__(self, url: str, status: int, message: str):
        super().__init__(f"HTTP {status} Error for {url}: {message}")


class PytoniqDependencyError(TonutilsException):
    """
    Exception raised when pytoniq dependency is missing.

    This exception informs the user that the pytoniq library is required
    and provides guidance on how to install it.
    """

    def __init__(self) -> None:
        super().__init__(
            "The 'pytoniq' library is required to use LiteserverClient functionality. "
            "Please install it with 'pip install tonutils[pytoniq]'."
        )
