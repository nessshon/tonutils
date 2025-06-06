# 🤖 TON Connect Demo Bot with Tonutils

[![TON](https://img.shields.io/badge/TON-grey?logo=TON&logoColor=40AEF0)](https://ton.org)
[![Telegram Bot](https://img.shields.io/badge/Bot-grey?logo=telegram)](https://core.telegram.org/bots)
[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License](https://img.shields.io/github/license/nessshon/token-access-control-bot)](https://github.com/nessshon/token-access-control-bot/blob/main/LICENSE)
[![Redis](https://img.shields.io/badge/Redis-Yes?logo=redis&color=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-blue?logo=docker&logoColor=white)](https://www.docker.com/)

TON Connect Demo Bot is a minimal example of integrating TON Connect with a Telegram bot using the [`tonutils`](https://github.com/nessshon/tonutils) Python SDK. It demonstrates how to connect a user's wallet, retrieve the address, and interact with the TON blockchain.

**Bot example:** [@tonconnect_demo_bot](https://t.me/tonconnect_demo_bot)

## Features

- Connects user wallets via TON Connect
- Built with `aiogram` (async Telegram bot framework)
- Stores session state in Redis
- Automatically pauses bridge session on user inactivity
- Docker-based deployment
- Clean modular structure ready for extension

## Getting Started

### Locate and configure

This bot is located inside the [`tonutils`](https://github.com/nessshon/tonutils) repository:

```bash
git clone https://github.com/nessshon/tonutils.git
cd tonutils/examples/tonconnect/telegram_bot
cp .env.example .env
```

Fill in the `.env` file with your actual bot token and manifest URL.
See [Environment Variables](#environment-variables) for details.

### Run the bot

Make sure Docker and Docker Compose are installed. Then launch:

```bash
docker-compose up --build
```

## Environment Variables

| Variable      | Description                                   | Example                                           |
| ------------- | --------------------------------------------- | ------------------------------------------------- |
| `BOT_TOKEN`   | Telegram Bot API token                        | `1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`   |
| `REDIS_DSN`   | Redis DSN used for session storage            | `redis://redis:6379/0`                            |
| `TC_MANIFEST` | Public URL to your `tonconnect-manifest.json` | `https://yourdomain.com/tonconnect-manifest.json` |

## Documentation

A detailed walkthrough of each module and the bot architecture is available in the
[TON Connect Telegram bot cookbook](https://nessshon.github.io/tonutils/cookbook/tonconnect-telegram/).

## Resources

* [TON Connect Documentation and Specifications](https://github.com/ton-blockchain/ton-connect)
* [tonutils TON Connect Documentation](https://nessshon.github.io/tonutils/cookbook/tonconnect-integration/)
* [aiogram Documentation](https://docs.aiogram.dev/)

## License

This project is distributed under the [MIT License](https://github.com/nessshon/tonutils/blob/main/LICENSE).
