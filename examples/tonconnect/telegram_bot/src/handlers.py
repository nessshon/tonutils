from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from pytoniq_core import begin_cell
from tonutils.tonconnect.models import (
    SignDataPayloadText,
    SignDataPayloadBinary,
    SignDataPayloadCell,
)
from tonutils.tonconnect.utils.exceptions import *
from tonutils.wallet.messages import TransferMessage

from .utils import windows, Context


async def start_command(message: Message, context: Context) -> None:
    """
    Handle /start command. Launch wallet connection or main menu.

    :param message: Incoming /start message.
    :param context: Execution context.
    """
    state_data = await context.state.get_data()
    rpc_request_id = state_data.get("rpc_request_id")

    if context.connector.is_request_pending(rpc_request_id):
        context.connector.cancel_pending_request(rpc_request_id)

    if not context.connector.connected:
        await windows.connect_wallet(context, message.from_user.id)
    else:
        await windows.wallet_connected(context, message.from_user.id)


async def callback_query_handler(callback_query: CallbackQuery, context: Context) -> None:
    """
    Handle all inline callback actions.

    :param callback_query: Incoming callback query.
    :param context: Execution context.
    """
    state_data = await context.state.get_data()
    rpc_request_id = state_data.get("rpc_request_id")
    data = callback_query.data

    if data.startswith("app_wallet:"):
        selected_wallet = data.split(":")[1]
        await context.state.update_data(selected_wallet=selected_wallet)
        await windows.connect_wallet(context, callback_query.from_user.id)

    elif data == "main_menu":
        await windows.wallet_connected(context, callback_query.from_user.id)

    elif data == "connect_wallet":
        await windows.connect_wallet(context, callback_query.from_user.id)

    elif data == "disconnect_wallet":
        await context.connector.disconnect_wallet()

    elif data == "cancel_transaction":
        if context.connector.pending_request_context(rpc_request_id):
            context.connector.cancel_pending_request(rpc_request_id)
        await windows.wallet_connected(context, callback_query.from_user.id)

    elif data == "send_transaction":
        rpc_request_id = await context.connector.send_transfer(
            destination=context.connector.account.address,
            amount=0.000000001,
            body="Hello from tonutils!",
        )
        await windows.send_request(context, callback_query.from_user.id)
        await context.state.update_data(rpc_request_id=rpc_request_id)

    elif data == "send_batch_transaction":
        max_messages = context.connector.device.get_max_supported_messages(context.connector.wallet)
        messages = [
            TransferMessage(
                destination=context.connector.account.address,
                amount=0.000000001,
                body="Hello from tonutils!",
            ) for _ in range(max_messages)
        ]
        rpc_request_id = await context.connector.send_batch_transfer(messages)
        await windows.send_request(context, callback_query.from_user.id)
        await context.state.update_data(rpc_request_id=rpc_request_id)

    elif data == "send_sign_data_request":
        await windows.choose_sign_data_type(context, callback_query.from_user.id)

    elif data.startswith("send_sign_data_request:"):
        payload_type = data.split(":")[1]
        payload_data = "Hello from tonutils!"

        if payload_type == "text":
            payload = SignDataPayloadText(text=payload_data)
        elif payload_type == "binary":
            payload = SignDataPayloadBinary(bytes=payload_data.encode())
        else:
            schema = "text_comment#00000000 text:Snakedata = InMsgBody;"
            cell = begin_cell().store_uint(0, 32).store_snake_string(payload_data).end_cell()
            payload = SignDataPayloadCell(cell=cell, schema=schema)

        try:
            context.connector.device.verify_sign_data_feature(
                context.connector.wallet, payload,
            )
            rpc_request_id = await context.connector.sign_data(payload)
            await context.state.update_data(rpc_request_id=rpc_request_id)
            await windows.send_request(context, callback_query.from_user.id)
        except WalletNotSupportFeatureError:
            await callback_query.answer("Your wallet does not support the sign data feature!", show_alert=True)

    await callback_query.answer()


def register_handlers(dp: Dispatcher) -> None:
    """
    Register bot handlers.

    :param dp: Aiogram dispatcher.
    """
    dp.message.register(start_command, CommandStart())
    dp.callback_query.register(callback_query_handler)


__all__ = ["register_handlers"]
