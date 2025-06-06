from contextlib import suppress

from .models import Context


async def delete_last_message(context: Context, user_id: int, message_id: int) -> None:
    """
    Delete the previously stored message and store the new one for future cleanup.

    :param context: Current context with bot and FSM state.
    :param user_id: Telegram user ID.
    :param message_id: New message ID to store.
    """
    state_data = await context.state.get_data()
    last_message_id = state_data.get("last_message_id")

    if last_message_id is not None:
        with suppress(Exception):
            await context.bot.delete_message(chat_id=user_id, message_id=last_message_id)

    await context.state.update_data(last_message_id=message_id)
