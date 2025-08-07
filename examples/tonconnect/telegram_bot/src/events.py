from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import (
    Event,
    EventError,
    SendTransactionResponse,
    SignDataResponse,
    WalletInfo, CheckProofRequestDto,
)
from tonutils.tonconnect.utils.exceptions import *
from tonutils.tonconnect.utils.verifiers import verify_ton_proof

from .utils import Context, windows


async def connect_event(user_id: int, wallet: WalletInfo, context: Context) -> None:
    """
    Called when the wallet is connected.

    :param user_id: Telegram user ID.
    :param wallet: Connected wallet information.
    :param context: Execution context.
    """
    payload = CheckProofRequestDto(
        address=wallet.account.address,
        public_key=wallet.account.public_key,
        state_init=wallet.account.state_init,
        proof=wallet.ton_proof,
    )
    if await verify_ton_proof(payload):
        await windows.wallet_connected(context, user_id)
    else:
        context.connector.add_event_kwargs(Event.DISCONNECT, failed_proof=True)
        await context.connector.disconnect_wallet()


async def connect_error(error: TonConnectError, user_id: int, context: Context) -> None:
    """
    Handle wallet connection errors.

    :param error: Exception from TonConnect.
    :param user_id: Telegram user ID.
    :param context: Execution context.
    """
    button_text, callback_data = "Try again", "connect_wallet"

    if isinstance(error, UserRejectsError):
        message_text = "You rejected the wallet connection."
    elif isinstance(error, RequestTimeoutError):
        message_text = "Connection request timed out."
    else:
        message_text = f"Connection error. Error: {error.message}"

    await windows.error(context, user_id, message_text, button_text, callback_data)


async def disconnect_event(user_id: int, context: Context, failed_proof: Optional[bool] = None) -> None:
    """
    Called when the wallet is disconnected.

    :param user_id: Telegram user ID.
    :param context: Execution context.
    :param failed_proof: Whether disconnection was triggered by invalid proof.
    """
    if failed_proof:
        message_text = "Wallet proof verification failed.\n\nPlease try again."
        await windows.error(context, user_id, message_text, "Try again", "connect_wallet")
    else:
        await windows.connect_wallet(context, user_id)


async def disconnect_error(error: TonConnectError, user_id: int, context: Context) -> None:
    """
    Handle wallet disconnection errors.

    :param error: Exception from TonConnect.
    :param user_id: Telegram user ID.
    :param context: Execution context.
    """
    button_text, callback_data = "Try again", "connect_wallet"

    if isinstance(error, UserRejectsError):
        message_text = "You rejected the wallet disconnection."
    elif isinstance(error, RequestTimeoutError):
        message_text = "Disconnect request timed out."
    else:
        message_text = f"Disconnect error. Error: {error.message}"

    await windows.error(context, user_id, message_text, button_text, callback_data)


async def transaction_event(user_id: int, transaction: SendTransactionResponse, context: Context) -> None:
    """
    Called when a transaction is sent successfully.

    :param user_id: Telegram user ID.
    :param transaction: Transaction result.
    :param context: Execution context.
    """
    await windows.transaction_sent(context, user_id, transaction)


async def transaction_error(error: TonConnectError, user_id: int, context: Context) -> None:
    """
    Handle errors during transaction.

    :param error: Exception from TonConnect.
    :param user_id: Telegram user ID.
    :param context: Execution context.
    """
    button_text, callback_data = "Try again", "main_menu"

    if isinstance(error, UserRejectsError):
        message_text = "You rejected the transaction."
    elif isinstance(error, RequestTimeoutError):
        message_text = "Transaction request timed out."
    else:
        message_text = f"Transaction error. Error: {error.message}"

    await windows.error(context, user_id, message_text, button_text, callback_data)


async def sign_data_event(user_id: int, sign_data: SignDataResponse, context: Context) -> None:
    """
    Called when sign data request completes successfully.

    :param user_id: Telegram user ID.
    :param sign_data: Sign data result.
    :param context: Execution context.
    """
    await windows.sign_data_sent(context, user_id, sign_data)


async def sign_data_error(error: TonConnectError, user_id: int, context: Context) -> None:
    """
    Handle errors during sign data request.

    :param error: Exception from TonConnect.
    :param user_id: Telegram user ID.
    :param context: Execution context.
    """
    button_text, callback_data = "Try again", "main_menu"

    if isinstance(error, UserRejectsError):
        message_text = "You rejected the data signing request."
    elif isinstance(error, RequestTimeoutError):
        message_text = "Data signing request timed out."
    else:
        message_text = f"Sign data error. Error: {error.message}"

    await windows.error(context, user_id, message_text, button_text, callback_data)


def register_events(tc: TonConnect) -> None:
    """
    Register all TonConnect event and error handlers.

    :param tc: TonConnect instance.
    """
    tc.register_event(Event.CONNECT, connect_event)
    tc.register_event(Event.DISCONNECT, disconnect_event)
    tc.register_event(Event.TRANSACTION, transaction_event)
    tc.register_event(Event.SIGN_DATA, sign_data_event)

    tc.register_event(EventError.CONNECT, connect_error)
    tc.register_event(EventError.DISCONNECT, disconnect_error)
    tc.register_event(EventError.TRANSACTION, transaction_error)
    tc.register_event(EventError.SIGN_DATA, sign_data_error)


__all__ = ["register_events"]
