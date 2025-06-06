import logging

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage as BotStorage
from redis.asyncio import Redis
from tonutils.tonconnect import TonConnect

from .events import register_events
from .handlers import register_handlers
from .middlewares import register_middlewares
from .session_manager import TonConnectSessionManager
from .utils.models import Config
from .utils.storage import RedisStorage as TCStorage


async def main() -> None:
    """
    Entry point for the bot application.
    Initializes config, Redis, TonConnect, dispatcher, and starts polling.
    """
    logging.basicConfig(level=logging.INFO)
    config = Config.load()

    # Redis connections for Aiogram FSM and TonConnect storage
    redis = Redis.from_url(url=config.REDIS_DSN)
    bot_storage = BotStorage(redis)
    tc_storage = TCStorage(redis)

    # Bot setup
    props = DefaultBotProperties(parse_mode="HTML")
    bot = Bot(token=config.BOT_TOKEN, default=props)

    # TonConnect setup
    tc = TonConnect(storage=tc_storage, manifest_url=config.TC_MANIFEST)
    tc_session_manager = TonConnectSessionManager(redis=redis, tc=tc)

    # Dispatcher
    dp = Dispatcher(storage=bot_storage, tc=tc, tc_session_manager=tc_session_manager)

    # Register handlers, events, and middleware
    register_events(tc)
    register_handlers(dp)
    register_middlewares(dp)
    tc_session_manager.run()

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
