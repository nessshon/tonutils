from typing import List

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from tonutils.tonconnect.models import WalletApp


def connect_wallet(wallets: List[WalletApp], selected_wallet: WalletApp, connect_url: str) -> InlineKeyboardMarkup:
    """
    Build a keyboard for selecting a wallet and connecting it.

    :param wallets: List of available wallet apps.
    :param selected_wallet: Currently selected wallet app.
    :param connect_url: Connection URL for the selected wallet.
    :return: Inline keyboard with wallet selection and connect button.
    """
    wallets_button = [
        InlineKeyboardButton(
            text=f"• {wallet.name} •" if wallet.app_name == selected_wallet.app_name else wallet.name,
            callback_data=f"app_wallet:{wallet.app_name}",
        ) for wallet in wallets
    ]
    connect_wallet_button = InlineKeyboardButton(
        text=f"Connect {selected_wallet.name}",
        url=connect_url,
    )
    builder = InlineKeyboardBuilder()
    builder.row(connect_wallet_button)
    builder.row(*wallets_button, width=2)

    return builder.as_markup()


def confirm_request(url: str, wallet_name: str) -> InlineKeyboardMarkup:
    """
    Build a keyboard to confirm or cancel the current request.

    :param url: URL to open the wallet for confirmation.
    :param wallet_name: Name of the wallet.
    :return: Inline keyboard with confirm and cancel buttons.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Open {wallet_name}", url=url)],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel_transaction")],
        ]
    )


def choose_action() -> InlineKeyboardMarkup:
    """
    Build the main menu keyboard for wallet actions.

    :return: Inline keyboard with wallet action options.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Send Transaction", callback_data="send_transaction"))
    builder.row(InlineKeyboardButton(text="Send Batch Transaction", callback_data="send_batch_transaction"))
    builder.row(InlineKeyboardButton(text="Send Sign Data Request", callback_data="send_sign_data_request"))
    builder.row(InlineKeyboardButton(text="Disconnect Wallet", callback_data="disconnect_wallet"))

    return builder.as_markup()


def choose_sign_data_type() -> InlineKeyboardMarkup:
    """
    Build a keyboard to choose a sign data format.

    :return: Inline keyboard with sign data format options.
    """
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Text", callback_data="send_sign_data_request:text"))
    builder.add(InlineKeyboardButton(text="Binary", callback_data="send_sign_data_request:binary"))
    builder.add(InlineKeyboardButton(text="Cell", callback_data="send_sign_data_request:cell"))
    builder.row(InlineKeyboardButton(text="Main Menu", callback_data="main_menu"))

    return builder.as_markup()


def go_to_main_menu() -> InlineKeyboardMarkup:
    """
    Build a keyboard with a single button to return to the main menu.

    :return: Inline keyboard with a main menu button.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Main Menu", callback_data="main_menu"))

    return builder.as_markup()
