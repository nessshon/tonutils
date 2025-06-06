from typing import Optional, Any, Dict, Type


class TonConnectError(Exception):
    prefix = "[TON Connect error]"

    def __repr__(self) -> str:
        return self.message

    def __init__(self, message: str, info: Optional[str] = None) -> None:
        self.message = message
        self.full_message = f"{self.prefix}: {message}"
        if info:
            self.full_message += f" ({info})"
        super().__init__(self.full_message)


class WalletAlreadyConnectedError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = ("Wallet connection called but wallet already connected. "
                     "To avoid the error, disconnect the wallet before doing a new connection.")
        super().__init__(message or "Wallet already connected.")


class WalletNotConnectedError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = "Send transaction or other protocol methods called while wallet is not connected."
        super().__init__(message or "Wallet not connected.")


class WalletNotSupportFeatureError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = "Wallet doesn't support the requested feature method."
        super().__init__(message or "Wallet doesn't support the requested feature method.")


class FetchWalletsError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = "An error occurred while fetching the wallets list."
        super().__init__(message or "Error fetching wallets list.")


class UnknownError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = "Unknown error."
        super().__init__(message or "Unknown error occurred.")


class BadRequestError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = "Request to the wallet contains errors."
        super().__init__(message or "Bad request error.")


class UnknownAppError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = "App tries to send RPC request to the injected wallet while not connected."
        super().__init__(message or "App RPC request error.")


class UserRejectsError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = "User rejects the action in the wallet."
        super().__init__(message or "User rejected the action.")


class RequestTimeoutError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = "Request timed out."
        super().__init__(message or "User did not respond within the predefined time limit.")


class ManifestNotFoundError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = ("Manifest not found. Make sure you added tonconnect-manifest.json "
                     "to the root of your app or passed correct manifest_url. See more at "
                     "https://github.com/ton-connect/docs/blob/main/requests-responses.md#app-manifest")
        super().__init__(message or "Manifest not found.")


class ManifestContentError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = ("The passed tonconnect-manifest.json contains errors. "
                     "Check the format of your manifest. See more at "
                     "https://github.com/ton-connect/docs/blob/main/requests-responses.md#app-manifest")
        super().__init__(message or "Manifest content error.")


class MethodNotSupportedError(TonConnectError):
    def __init__(self, message: Optional[str] = None) -> None:
        self.info = "The requested method is not supported by the wallet or is unknown."
        super().__init__(message or "Method not supported.")


class _EventError:
    ERRORS: Dict[int, Type[TonConnectError]]

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> Optional[TonConnectError]:
        from ..models import EventError

        error_data = response.get("error", {})
        if not error_data and response.get("event") in [
            EventError.CONNECT,
            EventError.DISCONNECT,
        ]:
            error_data = response.get("payload")

        if not error_data:
            return None

        message = error_data.get("message")
        code = error_data.get("code", 0)

        error_class = cls.ERRORS.get(code, UnknownError)
        return error_class(message)


class ConnectEventError(_EventError):
    ERRORS = {
        0: UnknownError,
        1: BadRequestError,
        2: ManifestNotFoundError,
        3: ManifestContentError,
        100: UnknownAppError,
        300: UserRejectsError,
        400: MethodNotSupportedError,
        500: RequestTimeoutError,
    }


class SendRequestEventError(_EventError):
    ERRORS = {
        0: UnknownError,
        1: BadRequestError,
        100: UnknownAppError,
        300: UserRejectsError,
        400: MethodNotSupportedError,
        500: RequestTimeoutError,
    }
