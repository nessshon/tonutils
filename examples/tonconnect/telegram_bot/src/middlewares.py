from contextlib import suppress
from typing import Callable, Dict, Any, Awaitable, Optional

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, User
from cachetools import TTLCache
from tonutils.tonconnect import TonConnect

from .session_manager import TonConnectSessionManager
from .utils.models import Context


class ContextMiddleware(BaseMiddleware):
    """
    Middleware to inject a custom Context object into handler data.
    """

    def __init__(self, tc_session_manager: TonConnectSessionManager) -> None:
        self.tc_session_manager = tc_session_manager

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        """
        Inject context if event is from a valid user.

        :param handler: Event handler to call next.
        :param event: Incoming Telegram update.
        :param data: Handler context data.
        :return: Handler result.
        """
        user: User = data.get("event_from_user")

        if user and not user.is_bot:
            await self.tc_session_manager.update(user.id)

            bot: Bot = data.get("bot")
            tc: TonConnect = data.get("tc")
            state: FSMContext = data.get("state")
            connector = await tc.init_connector(user.id)

            context = Context(
                bot=bot,
                state=state,
                tc=tc,
                connector=connector,
            )

            tc["context"] = context
            data["context"] = context

        return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    """
    Middleware to prevent spam by throttling user input.
    """

    def __init__(self, ttl: float = 0.7) -> None:
        """
        :param ttl: Time-to-live in seconds for each user.
        """
        self.cache = TTLCache(maxsize=10_000, ttl=ttl)

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Optional[Any]:
        """
        Block repeated events from the same user within TTL.

        :param handler: Event handler to call next.
        :param event: Incoming Telegram update.
        :param data: Handler context data.
        :return: Handler result or None if throttled.
        """
        user: Optional[User] = data.get("event_from_user")

        if user and user.id in self.cache:
            with suppress(Exception):
                await getattr(event, "message", None).delete()
            return None

        if user:
            self.cache[user.id] = None

        return await handler(event, data)


def register_middlewares(dp: Dispatcher) -> None:
    """
    Register all middlewares in the dispatcher.

    :param dp: Aiogram dispatcher instance.
    """
    dp.update.middleware.register(ContextMiddleware(dp["tc_session_manager"]))
    dp.update.middleware.register(ThrottlingMiddleware())


__all__ = ["register_middlewares"]
