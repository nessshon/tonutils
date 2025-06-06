from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from environs import Env
from tonutils.tonconnect import TonConnect, Connector


@dataclass
class Context:
    """
    Aggregated context object passed throughout the bot's logic.

    :param bot: The bot instance used to send and receive messages.
    :param state: Finite State Machine context for user session management.
    :param tc: Instance of TonConnect for managing wallet connections.
    :param connector: Connector used to communicate with a specific wallet.
    """
    bot: Bot
    state: FSMContext
    tc: TonConnect
    connector: Connector


@dataclass
class Config:
    """
    Configuration data loaded from the environment.

    :param BOT_TOKEN: Telegram bot token.
    :param REDIS_DSN: Redis connection string for FSM or other caching.
    :param TC_MANIFEST: URL to the TonConnect manifest file.
    """
    BOT_TOKEN: str
    REDIS_DSN: str
    TC_MANIFEST: str

    @classmethod
    def load(cls) -> Config:
        """
        Loads configuration from environment variables using .env file.

        :return: An instance of Config populated with environment values.
        """
        env = Env()
        env.read_env()

        return cls(
            BOT_TOKEN=env.str("BOT_TOKEN"),
            REDIS_DSN=env.str("REDIS_DSN"),
            TC_MANIFEST=env.str("TC_MANIFEST"),
        )
