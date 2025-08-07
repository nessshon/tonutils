import base64
import json

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hide_link, hblockquote, hbold

from tonutils.tonconnect.models import Event, SendTransactionResponse, SignDataResponse, CheckSignDataRequestDto
from tonutils.tonconnect.utils import generate_proof_payload
from tonutils.tonconnect.utils.verifiers import verify_sign_data
from ..utils import Context, delete_last_message
from ..utils import keyboards


async def connect_wallet(context: Context, user_id: int) -> None:
    """
    Show wallet selection and QR code for connection.

    :param context: Execution context.
    :param user_id: Telegram user ID.
    """
    state_data = await context.state.get_data()
    wallets = await context.tc.get_wallets()
    selected_wallet_name = state_data.get("selected_wallet", wallets[0].app_name)

    selected_wallet = next((w for w in wallets if w.app_name == selected_wallet_name), wallets[0])
    redirect_url = "https://t.me/tonconnect_demo_bot"
    payload_hex, payload_hash = generate_proof_payload()

    await context.state.update_data(ton_proof=payload_hex)
    context.connector.add_event_kwargs(Event.CONNECT, state=context.state)

    connect_url = await context.connector.connect_wallet(
        wallet_app=selected_wallet,
        redirect_url=redirect_url,
        ton_proof=payload_hex,
    )

    qrcode_url = (
        f"https://qrcode.ness.su/create?"
        f"box_size=20&border=7&image_padding=20"
        f"&data={base64.b64encode(connect_url.encode()).decode()}"
        f"&image_url={base64.b64encode(selected_wallet.image.encode()).decode()}"
    )

    text = f"{hide_link(qrcode_url)}<b>Connect your wallet!</b>"
    reply_markup = keyboards.connect_wallet(wallets, selected_wallet, connect_url)

    message = await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(context, user_id, message.message_id)


async def wallet_connected(context: Context, user_id: int) -> None:
    """
    Show connected wallet address and main menu.

    :param context: Execution context.
    :param user_id: Telegram user ID.
    """
    wallet_address = context.connector.wallet.account.address.to_str(is_bounceable=False)
    reply_markup = keyboards.choose_action()
    text = f"<b>Connected wallet:</b>\n{hblockquote(wallet_address)}\n\nChoose an action:"

    message = await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(context, user_id, message.message_id)


async def send_request(context: Context, user_id: int) -> None:
    """
    Prompt user to confirm the request in wallet.

    :param context: Execution context.
    :param user_id: Telegram user ID.
    """
    reply_markup = keyboards.confirm_request(
        url=context.connector.wallet_app.direct_url,
        wallet_name=context.connector.wallet_app.name,
    )
    text = "<b>Please confirm the request in your wallet.</b>"

    message = await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(context, user_id, message.message_id)


async def transaction_sent(context: Context, user_id: int, transaction: SendTransactionResponse) -> None:
    """
    Show transaction confirmation and details.

    :param context: Execution context.
    :param user_id: Telegram user ID.
    :param transaction: Transaction result.
    """
    text = (
        "<b>Transaction sent!</b>\n\n"
        f"Normalized hash:\n{hblockquote(transaction.normalized_hash)}\n"
        f"BoC:\n{hblockquote(transaction.boc)}\n"
    )
    reply_markup = keyboards.go_to_main_menu()

    message = await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(context, user_id, message.message_id)


async def choose_sign_data_type(context: Context, user_id: int) -> None:
    """
    Show menu to select data type for signing.

    :param context: Execution context.
    :param user_id: Telegram user ID.
    """
    text = "<b>Choose the type of data you want to sign:</b>"
    reply_markup = keyboards.choose_sign_data_type()

    message = await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(context, user_id, message.message_id)


async def sign_data_sent(context: Context, user_id: int, sign_data: SignDataResponse) -> None:
    """
    Show signed data result and verification.

    :param context: Execution context.
    :param user_id: Telegram user ID.
    :param sign_data: Sign data result.
    """
    payload = CheckSignDataRequestDto(
        state_init=context.connector.account.state_init,
        public_key=context.connector.account.public_key,
        result=sign_data.result,
    )
    if await verify_sign_data(payload):
        text = (
            "<b>Data successfully signed!</b>\n\n"
            f"Payload:\n{hblockquote(json.dumps(sign_data.result.payload.to_dict(), indent=4))}"
        )
    else:
        text = (
            "<b>Failed to verify the signed data.</b>\n"
            "The signature may be invalid or tampered."
        )

    reply_markup = keyboards.go_to_main_menu()

    message = await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(context, user_id, message.message_id)


async def error(context: Context, user_id: int, message_text: str, button_text: str, callback_data: str) -> None:
    """
    Show error message with a retry button.

    :param context: Execution context.
    :param user_id: Telegram user ID.
    :param message_text: Text to show in the error message.
    :param button_text: Text for the retry button.
    :param callback_data: Callback data for retry action.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    reply_markup = builder.as_markup()

    message = await context.bot.send_message(chat_id=user_id, text=hbold(message_text), reply_markup=reply_markup)
    await delete_last_message(context, user_id, message.message_id)
