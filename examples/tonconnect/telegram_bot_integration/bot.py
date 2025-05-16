import base64
from contextlib import suppress
from typing import List

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hide_link, hcode
from redis.asyncio import Redis

from storage import TCRedisStorage
from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import WalletApp, Event, EventError, SendTransactionResponse
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError, RequestTimeoutError
from tonutils.wallet.messages import TransferMessage

BOT_TOKEN = "your bot token"
REDIS_DSN = "redis://localhost:6379"
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"

redis = Redis.from_url(url=REDIS_DSN)
dp = Dispatcher(storage=RedisStorage(redis))
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
tc = TonConnect(storage=TCRedisStorage(redis), manifest_url=TC_MANIFEST_URL,
                wallets_fallback_file_path="./wallets.json")


async def delete_last_message(user_id: int, message_id: int) -> None:
    state = dp.fsm.resolve_context(bot, user_id, user_id)
    last_message_id = (await state.get_data()).get("last_message_id")

    if last_message_id is not None:
        with suppress(Exception):
            await bot.delete_message(chat_id=user_id, message_id=last_message_id)

    await state.update_data(last_message_id=message_id)


def _connect_wallet_markup(
        wallets: List[WalletApp],
        selected_wallet: WalletApp,
        connect_url: str,
) -> InlineKeyboardMarkup:
    wallets_button = [
        *[
            InlineKeyboardButton(
                text=f"• {wallet.name} •" if wallet.app_name == selected_wallet.app_name else wallet.name,
                callback_data=f"app_wallet:{wallet.app_name}",
            ) for wallet in wallets
        ]
    ]
    connect_wallet_button = InlineKeyboardButton(
        text=f"Connect {selected_wallet.name}",
        url=connect_url,
    )
    builder = InlineKeyboardBuilder()
    builder.row(connect_wallet_button)
    builder.row(*wallets_button, width=2)

    return builder.as_markup()


def _confirm_transaction_markup(url: str, wallet_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Open {wallet_name}", url=url)],
            [InlineKeyboardButton(text=f"Cancel", callback_data="cancel_transaction")],
        ]
    )


def _choose_action_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Send transaction", callback_data="send_transaction"))
    builder.row(InlineKeyboardButton(text="Send batch transaction", callback_data="send_batch_transaction"))
    builder.row(InlineKeyboardButton(text="Disconnect wallet", callback_data="disconnect_wallet"))

    return builder.as_markup()


def _go_to_main_menu_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Main menu", callback_data="main_menu"))

    return builder.as_markup()


async def connect_wallet_window(state: FSMContext, user_id: int) -> None:
    connector = await tc.init_connector(user_id)
    state_data = await state.get_data()
    wallets = await tc.get_wallets()

    selected_wallet = state_data.get("selected_wallet", wallets[0].app_name)
    selected_wallet = next(w for w in wallets if w.app_name == selected_wallet)
    connect_url = await connector.connect_wallet(wallet_app=selected_wallet)

    qrcode_url = (
        f"https://qrcode.ness.su/create?"
        f"box_size=20&border=7&image_padding=20"
        f"&data={base64.b64encode(connect_url.encode()).decode()}"
        f"&image_url={base64.b64encode(selected_wallet.image.encode()).decode()}"
    )

    text = f"{hide_link(qrcode_url)}Connect your wallet!"
    reply_markup = _connect_wallet_markup(wallets, selected_wallet, connect_url)

    message = await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)


async def wallet_connected_window(user_id: int) -> None:
    connector = await tc.init_connector(user_id)
    wallet_address = connector.wallet.account.address.to_str(is_bounceable=False)

    reply_markup = _choose_action_markup()
    text = f"Connected wallet:\n{hcode(wallet_address)}\n\nChoose an action:"

    message = await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)


async def send_transaction_window(user_id: int) -> None:
    connector = await tc.init_connector(user_id)
    reply_markup = _confirm_transaction_markup(
        url=connector.wallet_app.direct_url,
        wallet_name=connector.wallet_app.name,
    )

    text = "Please confirm the transaction in your wallet."

    message = await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)


async def transaction_sent_window(user_id: int, transaction: SendTransactionResponse) -> None:
    text = (
        "Transaction sent!\n\n"
        f"Transaction msg hash:\n{hcode(transaction.normalized_hash)}\n"
        f"Transaction BoC:\n{hcode(transaction.boc)}\n"
    )
    reply_markup = _go_to_main_menu_markup()

    message = await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)


async def error_window(user_id: int, message_text: str, button_text: str, callback_data: str) -> None:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    reply_markup = builder.as_markup()

    message = await bot.send_message(chat_id=user_id, text=message_text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)


@tc.on_event(Event.CONNECT)
async def connect_event(user_id: int) -> None:
    await wallet_connected_window(user_id)


@tc.on_event(EventError.CONNECT)
async def connect_error_event(error: TonConnectError, user_id: int) -> None:
    button_text, callback_data = "Try again", "connect_wallet"
    if isinstance(error, UserRejectsError):
        message_text = f"You rejected the wallet connection."
    elif isinstance(error, RequestTimeoutError):
        message_text = f"Connection request timed out."
    else:
        message_text = f"Connection error. Error: {error.message}"
    await error_window(user_id, message_text, button_text, callback_data)


@tc.on_event(Event.DISCONNECT)
async def disconnect_event(user_id: int) -> None:
    state = dp.fsm.resolve_context(bot, user_id, user_id)
    await connect_wallet_window(state, user_id)


@tc.on_event(EventError.DISCONNECT)
async def disconnect_error_event(error: TonConnectError, user_id: int) -> None:
    button_text, callback_data = "Try again", "connect_wallet"
    if isinstance(error, UserRejectsError):
        message_text = f"You rejected the wallet disconnection."
    elif isinstance(error, RequestTimeoutError):
        message_text = f"Disconnect request timed out."
    else:
        message_text = f"Disconnect error. Error: {error.message}"

    await error_window(user_id, message_text, button_text, callback_data)


@tc.on_event(Event.TRANSACTION)
async def transaction_event(user_id: int, transaction: SendTransactionResponse) -> None:
    await transaction_sent_window(user_id, transaction)


@tc.on_event(EventError.TRANSACTION)
async def transaction_error_event(error: TonConnectError, user_id: int) -> None:
    button_text, callback_data = "Try again", "main_menu"
    if isinstance(error, UserRejectsError):
        message_text = f"You rejected the transaction."
    elif isinstance(error, RequestTimeoutError):
        message_text = f"Transaction request timed out."
    else:
        message_text = f"Transaction error. Error: {error.message}"

    await error_window(user_id, message_text, button_text, callback_data)


@dp.message(CommandStart())
async def start_command(message: Message, state: FSMContext) -> None:
    connector = await tc.init_connector(message.from_user.id)
    rpc_request_id = (await state.get_data()).get("rpc_request_id")
    if connector.is_transaction_pending(rpc_request_id):
        connector.cancel_pending_transaction(rpc_request_id)

    if not connector.connected:
        await connect_wallet_window(state, message.from_user.id)
    else:
        await wallet_connected_window(message.from_user.id)


@dp.callback_query()
async def callback_query_handler(callback_query: CallbackQuery, state: FSMContext) -> None:
    connector = await tc.init_connector(callback_query.from_user.id)
    rpc_request_id = (await state.get_data()).get("rpc_request_id")

    if callback_query.data.startswith("app_wallet:"):
        selected_wallet = callback_query.data.split(":")[1]
        await state.update_data(selected_wallet=selected_wallet)
        await connect_wallet_window(state, callback_query.from_user.id)

    elif callback_query.data == "main_menu":
        await wallet_connected_window(callback_query.from_user.id)

    elif callback_query.data == "connect_wallet":
        await connect_wallet_window(state, callback_query.from_user.id)

    elif callback_query.data == "disconnect_wallet":
        connector.add_event_kwargs(Event.DISCONNECT, state=state)
        await connector.disconnect_wallet()

    elif callback_query.data == "cancel_transaction":
        if connector.is_transaction_pending(rpc_request_id):
            connector.cancel_pending_transaction(rpc_request_id)
        await wallet_connected_window(callback_query.from_user.id)

    elif callback_query.data == "send_transaction":
        rpc_request_id = await connector.send_transfer(
            destination=connector.account.address,
            amount=0.000000001,
            body="Hello from tonutils!",
        )
        await send_transaction_window(callback_query.from_user.id)
        await state.update_data(rpc_request_id=rpc_request_id)

    elif callback_query.data == "send_batch_transaction":
        messages = [
            TransferMessage(
                destination=connector.account.address,
                amount=0.000000001,
                body="Hello from tonutils!",
            ) for _ in range(4)
        ]
        rpc_request_id = await connector.send_batch_transfer(messages)
        await send_transaction_window(callback_query.from_user.id)
        await state.update_data(rpc_request_id=rpc_request_id)

    await callback_query.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
