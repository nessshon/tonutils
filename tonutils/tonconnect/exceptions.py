import typing as t

__all__ = [
    "BadRequestError",
    "FetchWalletsError",
    "ManifestContentError",
    "ManifestNotFoundError",
    "MethodNotSupportedError",
    "RequestTimeoutError",
    "TonConnectError",
    "TonConnectErrors",
    "UnknownAppError",
    "UnknownError",
    "UserRejectsError",
    "WalletAlreadyConnectedError",
    "WalletMissingRequiredFeaturesError",
    "WalletNotConnectedError",
    "WalletNotSupportFeatureError",
    "WalletWrongNetworkError",
]


class TonConnectError(Exception):
    """Base exception for all TonConnect errors."""

    default_message: t.ClassVar[str] = "TonConnect error."
    default_info: t.ClassVar[t.Optional[str]] = None

    code: int
    message: str
    info: t.Optional[str]

    def __init__(
        self,
        message: t.Optional[str] = None,
        *,
        code: int = 0,
        info: t.Optional[str] = None,
    ) -> None:
        """
        :param message: Error description, or `None` for `default_message`.
        :param code: Numeric RPC error code.
        :param info: Extended explanation, or `None` for `default_info`.
        """
        self.code = int(code)
        self.message = message or self.default_message
        self.info = self.default_info if info is None else info

        text = self.message
        if self.info:
            text = f"{text} ({self.info})"
        super().__init__(text)


class WalletAlreadyConnectedError(TonConnectError):
    """Wallet is already connected."""

    default_message = "Wallet already connected."
    default_info = (
        "Wallet connection called but wallet already connected. "
        "To avoid the error, disconnect the wallet before doing a new connection."
    )


class WalletNotConnectedError(TonConnectError):
    """No wallet connected for the requested RPC method."""

    default_message = "Wallet not connected."
    default_info = "Send transaction or other protocol methods called while wallet is not connected."


class WalletMissingRequiredFeaturesError(TonConnectError):
    """Wallet does not declare minimum required features."""

    default_message = "Missing required features."
    default_info = "Update the wallet application."


class WalletNotSupportFeatureError(TonConnectError):
    """Wallet does not support the requested feature or capability."""

    default_message = "Wallet doesn't support the requested feature method."
    default_info = "Wallet doesn't support the requested feature method."


class WalletWrongNetworkError(TonConnectError):
    """Wallet operates on a different network than expected."""

    default_message = "Wallet connected to wrong network."
    default_info = "Switch the wallet network and try again."


class FetchWalletsError(TonConnectError):
    """Wallets list could not be fetched or parsed."""

    default_message = "Failed to fetch wallets list."
    default_info = "An error occurred while fetching the wallets list."


class UnknownError(TonConnectError):
    """Unrecognised TonConnect RPC error (code 0)."""

    default_message = "Unknown error occurred."
    default_info = "Unknown error."


class BadRequestError(TonConnectError):
    """Malformed RPC request (code 1)."""

    default_message = "Bad request."
    default_info = "Request to the wallet contains errors."


class UnknownAppError(TonConnectError):
    """RPC request from an unconnected app (code 100)."""

    default_message = "App RPC request error."
    default_info = (
        "App tries to send RPC request to the injected wallet while not connected."
    )


class UserRejectsError(TonConnectError):
    """User rejected the action in the wallet UI (code 300)."""

    default_message = "User rejected the action."
    default_info = "User rejects the action in the wallet."


class ManifestNotFoundError(TonConnectError):
    """Wallet could not fetch `tonconnect-manifest.json` (code 2)."""

    default_message = "Manifest not found."
    default_info = (
        "Make sure you added tonconnect-manifest.json to the root of your app "
        "or passed correct manifest_url. See more at "
        "https://github.com/ton-connect/docs/blob/main/requests-responses.md#app-manifest"
    )


class ManifestContentError(TonConnectError):
    """`tonconnect-manifest.json` content is invalid (code 3)."""

    default_message = "Manifest content error."
    default_info = (
        "The passed tonconnect-manifest.json contains errors. "
        "Check the format of your manifest. See more at "
        "https://github.com/ton-connect/docs/blob/main/requests-responses.md#app-manifest"
    )


class MethodNotSupportedError(TonConnectError):
    """Wallet does not support the requested RPC method (code 400)."""

    default_message = "Method not supported."
    default_info = "The requested method is not supported by the wallet or is unknown."


class RequestTimeoutError(TonConnectError):
    """User did not respond within the time limit (code 500)."""

    default_message = "Request timed out."
    default_info = "User did not respond within the predefined time limit."


class TonConnectErrors:
    """Map TonConnect RPC error codes to typed exceptions."""

    CODE_TO_ERROR: t.ClassVar[t.Dict[int, t.Type[TonConnectError]]] = {
        0: UnknownError,
        1: BadRequestError,
        2: ManifestNotFoundError,
        3: ManifestContentError,
        100: UnknownAppError,
        300: UserRejectsError,
        400: MethodNotSupportedError,
        500: RequestTimeoutError,
    }

    @classmethod
    def from_code(cls, code: int, message: str) -> TonConnectError:
        """Create a typed `TonConnectError` from an RPC error code.

        :param code: Numeric error code from the wallet.
        :param message: Error message from the wallet.
        :return: Corresponding exception instance.
        """
        exc_type = cls.CODE_TO_ERROR.get(int(code), TonConnectError)
        return exc_type(message, code=int(code))
