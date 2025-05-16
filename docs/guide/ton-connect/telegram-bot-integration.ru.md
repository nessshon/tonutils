Это руководство содержит пошаговые инструкции по интеграции и управлению подключением кошельков и отправкой транзакций в
Telegram-боте с использованием `TonConnect` из библиотеки `tonutils`. Независимо от того, являетесь ли вы начинающим или
опытным разработчиком, это руководство поможет вам эффективно реализовать функциональность подключения кошельков и
работы с
транзакциями в вашем Telegram-боте.

## Установка

Установите необходимые Python-библиотеки с помощью `pip`:

```bash
pip install tonutils aiogram redis
```

## Структура

Организуйте файлы проекта следующим образом:

```
telegram-tonconnect-bot/
├── bot.py
├── storage.py
```

* **bot.py**: Основной скрипт бота, содержащий всю логику.
* **storage.py**: Пользовательская реализация хранилища для TonConnect.

## Конфигурация

### Создание манифеста TonConnect

Создайте JSON-файл, описывающий ваше приложение. Он будет отображаться в кошельке при подключении.

    {
      "url": "<app-url>",                        // required
      "name": "<app-name>",                      // required
      "iconUrl": "<app-icon-url>",               // required
      "termsOfUseUrl": "<terms-of-use-url>",     // optional
      "privacyPolicyUrl": "<privacy-policy-url>" // optional
    }

!!! note
    Убедитесь, что файл доступен по-указанному URL.

### Реализация хранилища

TonConnect требует систему хранения для управления своими данными. Здесь представлена реализация хранилища на основе
Redis.

```python
# storage.py

from typing import Optional

from redis.asyncio import Redis

from tonutils.tonconnect import IStorage


class TCRedisStorage(IStorage):
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def set_item(self, key: str, value: str) -> None:
        await self.redis.set(name=key, value=value)

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        value = await self.redis.get(name=key)
        return value.decode() if value else default_value

    async def remove_item(self, key: str) -> None:
        await self.redis.delete(key)
```

### Инициализация

Создайте Python-скрипт и выполните начальную настройку.

```python
# bot.py

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
from tonutils.wallet.data import TransferMessage

BOT_TOKEN = "your bot token"
REDIS_DSN = "redis://localhost:6379"
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"

# Initialize Redis
redis = Redis.from_url(url=REDIS_DSN)

# Initialize Dispatcher with Redis Storage
dp = Dispatcher(storage=RedisStorage(redis))

# Initialize Telegram Bot
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))

# Initialize TonConnect
tc = TonConnect(storage=TCRedisStorage(redis), manifest_url=TC_MANIFEST_URL,
                wallets_fallback_file_path="./wallets.json")
```

* **Инициализация Redis**: Устанавливает соединение с сервером Redis.
* **Инициализация Dispatcher и бота**: Настраивает диспетчер с использованием Redis-хранилища и инициализирует бота.
* **Инициализация TonConnect**: Настраивает TonConnect с пользовательским Redis-хранилищем и URL манифеста.

## Вспомогательные функции бота

### Клавиатуры

Функции для создания различных inline-клавиатур, используемых в боте.

#### Клавиатура подключения кошелька

Создаёт inline-клавиатуру для выбора и подключения кошельков.

```python
def _connect_wallet_markup(
        wallets: List[WalletApp],
        selected_wallet: WalletApp,
        connect_url: str,
) -> InlineKeyboardMarkup:
    wallets_buttons = [
        InlineKeyboardButton(
            text=f"• {wallet.name} •" if wallet.app_name == selected_wallet.app_name else wallet.name,
            callback_data=f"app_wallet:{wallet.app_name}",
        )
        for wallet in wallets
    ]
    connect_wallet_button = InlineKeyboardButton(
        text=f"Connect {selected_wallet.name}",
        url=connect_url,
    )
    builder = InlineKeyboardBuilder()
    builder.row(connect_wallet_button)
    builder.row(*wallets_buttons, width=2)

    return builder.as_markup()
```

* **Кнопки кошельков:** Отображают список доступных кошельков, выделяя выбранный.
* **Кнопка подключения:** Предоставляет прямую ссылку для подключения выбранного кошелька.
* **Разметка:** Использует `InlineKeyboardBuilder` для аккуратной организации кнопок.

#### Клавиатура подтверждения транзакции

Создаёт inline-клавиатуру для подтверждения или отмены транзакции.

```python
def _confirm_transaction_markup(url: str, wallet_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Open {wallet_name}", url=url)],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel_transaction")],
        ]
    )
```

* **Кнопка открытия кошелька:** Перенаправляет пользователя в кошелёк для подтверждения транзакции.
* **Кнопка отмены:** Позволяет пользователю отменить ожидающую транзакцию.

#### Клавиатура выбора действия

Создаёт inline-клавиатуру для выбора действий после подключения кошелька.

```python
def _choose_action_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Send transaction", callback_data="send_transaction"))
    builder.row(InlineKeyboardButton(text="Send batch transaction", callback_data="send_batch_transaction"))
    builder.row(InlineKeyboardButton(text="Disconnect wallet", callback_data="disconnect_wallet"))

    return builder.as_markup()
```

* **Действия:** Пользователь может выбрать отправку одной транзакции, пакетную отправку нескольких транзакций или
  отключение кошелька.

#### Клавиатура возврата в главное меню

Создаёт inline-клавиатуру для возврата в главное меню.

```python
def _go_to_main_menu_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Main menu", callback_data="main_menu"))

    return builder.as_markup()
```

* **Кнопка главного меню:** Позволяет пользователю вернуться к основному интерфейсу.

### Окна

Определяют различные интерфейсные окна, которые реагируют на действия пользователя и события TonConnect.

#### Окно подключения кошелька

Отображает пользователю интерфейс для подключения кошелька.

```python
async def connect_wallet_window(state: FSMContext, user_id: int) -> None:
    connector = await tc.init_connector(user_id)
    state_data = await state.get_data()
    wallets = await tc.get_wallets()

    selected_wallet = state_data.get("selected_wallet", wallets[0].app_name)
    selected_wallet = next(wallet for wallet in wallets if wallet.app_name == selected_wallet)
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
```

* **Инициализация коннектора:** Подготавливает коннектор TonConnect для пользователя.
* **Выбор кошелька:** Получает список доступных кошельков и выбирает предпочтительный.
* **Генерация QR-кода:** Формирует ссылку с QR-кодом для подключения кошелька.
* **Запрос к пользователю:** Отправляет сообщение с предложением подключить кошелёк и соответствующей
  inline-клавиатурой.

#### Окно подключённого кошелька

Отображает информацию о подключённом кошельке и доступные действия.

```python
async def wallet_connected_window(user_id: int) -> None:
    connector = await tc.init_connector(user_id)
    wallet_address = connector.wallet.account.address.to_str(is_bounceable=False)

    reply_markup = _choose_action_markup()
    text = f"Connected wallet:\n{hcode(wallet_address)}\n\nChoose an action:"

    message = await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)
```

* **Информация о кошельке:** Показывает адрес подключённого кошелька.
* **Доступные действия:** Предлагает варианты — отправить транзакцию, выполнить пакетную отправку или отключить кошелёк.

#### Окно отправки транзакции

Запрашивает у пользователя подтверждение транзакции в кошельке.

```python
async def send_transaction_window(user_id: int) -> None:
    connector = await tc.init_connector(user_id)
    reply_markup = _confirm_transaction_markup(
        url=connector.wallet_app.direct_url,
        wallet_name=connector.wallet_app.name,
    )

    text = "Please confirm the transaction in your wallet."

    message = await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)
```

* **Запрос пользователю:** Предлагает пользователю подтвердить транзакцию в своём кошельке.
* **Варианты подтверждения:** Предоставляет кнопки для открытия кошелька или отмены транзакции.

#### Окно успешной отправки транзакции

Отображает детали транзакции после её успешной отправки.

```python
async def transaction_sent_window(user_id: int, transaction: SendTransactionResponse) -> None:
    text = (
        "Transaction sent!\n\n"
        f"Transaction msg hash:\n{hcode(transaction.normalized_hash)}\n"
        f"Transaction BoC:\n{hcode(transaction.boc)}\n"
    )
    reply_markup = _go_to_main_menu_markup()

    message = await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)
```

* **Детали транзакции:** Показывает хеш транзакции и BoC (Bag of Cells) для справки.
* **Навигация:** Предоставляет кнопку для возврата в главное меню.

#### Окно ошибки

Отображает сообщение об ошибке с возможностью повторить попытку или вернуться назад.

```python
async def error_window(user_id: int, message_text: str, button_text: str, callback_data: str) -> None:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    reply_markup = builder.as_markup()

    message = await bot.send_message(chat_id=user_id, text=message_text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)
```

* **Сообщение об ошибке:** Информирует пользователя о возникшей проблеме.
* **Кнопка повтора:** Позволяет повторить неудачное действие или вернуться к другому разделу.

### Утилиты

Функция для удаления последнего отправленного сообщения пользователю с целью поддержания чистоты в чате.

```python
async def delete_last_message(user_id: int, message_id: int) -> None:
    state = dp.fsm.resolve_context(bot, user_id, user_id)
    last_message_id = (await state.get_data()).get("last_message_id")

    if last_message_id is not None:
        with suppress(Exception):
            await bot.delete_message(chat_id=user_id, message_id=last_message_id)

    await state.update_data(last_message_id=message_id)
```

* **Назначение**: Обеспечивает отображение только последнего сообщения для пользователя, улучшая пользовательский опыт.
* **Функциональность**:
    * Извлекает ID последнего сообщения из состояния пользователя.
    * Пытается удалить предыдущее сообщение, если оно существует.
    * Обновляет состояние новым ID сообщения.

## Обработчики TonConnect

TonConnect использует события для обработки различных действий, связанных с кошельком. В
этом разделе описано, как обрабатывать такие события внутри вашего бота.

#### Событие подключения

Обработчик события успешного подключения кошелька.

```python
@tc.on_event(Event.CONNECT)
async def connect_event(user_id: int) -> None:
    await wallet_connected_window(user_id)
```

* **Триггер:** Срабатывает при успешном подключении кошелька.
* **Действие:** Показывает пользователю информацию о подключённом кошельке и доступные действия.

#### Событие ошибки подключения

Обработчик ошибок, возникающих при подключении кошелька.

```python
@tc.on_event(EventError.CONNECT)
async def connect_error_event(error: TonConnectError, user_id: int) -> None:
    button_text, callback_data = "Try again", "connect_wallet"
    if isinstance(error, UserRejectsError):
        message_text = "You rejected the wallet connection."
    elif isinstance(error, RequestTimeoutError):
        message_text = "Connection request timed out."
    else:
        message_text = f"Connection error. Error: {error.message}"
    await error_window(user_id, message_text, button_text, callback_data)
```

* **Типы ошибок:**
    * **UserRejectsError:** Пользователь отклонил подключение.
    * **RequestTimeoutError:** Время ожидания подключения истекло.
    * **Другие ошибки:** Общие проблемы при подключении.
* **Действие:** Показывает сообщение об ошибке с возможностью повторить попытку.

#### Событие отключения

Обработчик события успешного отключения кошелька.

```python
@tc.on_event(Event.DISCONNECT)
async def disconnect_event(user_id: int) -> None:
    state = dp.fsm.resolve_context(bot, user_id, user_id)
    await connect_wallet_window(state, user_id)
```

* **Триггер:** Срабатывает при успешном отключении кошелька.
* **Действие:** Предлагает пользователю повторно подключить кошелёк.

#### Событие ошибки отключения

Обработчик ошибок, возникающих при отключении кошелька.

```python
@tc.on_event(EventError.DISCONNECT)
async def disconnect_error_event(error: TonConnectError, user_id: int) -> None:
    button_text, callback_data = "Try again", "connect_wallet"
    if isinstance(error, UserRejectsError):
        message_text = "You rejected the wallet disconnection."
    elif isinstance(error, RequestTimeoutError):
        message_text = "Disconnect request timed out."
    else:
        message_text = f"Disconnect error. Error: {error.message}"

    await error_window(user_id, message_text, button_text, callback_data)
```

* **Типы ошибок:**
    * **UserRejectsError:** Пользователь отклонил отключение.
    * **RequestTimeoutError:** Время ожидания запроса на отключение истекло.
    * **Другие ошибки:** Общие проблемы при отключении.
* **Действие:** Показывает сообщение об ошибке с возможностью повторить попытку.

#### Событие транзакции

Обработчик события успешной отправки транзакции.

```python
@tc.on_event(Event.TRANSACTION)
async def transaction_event(user_id: int, transaction: SendTransactionResponse) -> None:
    await transaction_sent_window(user_id, transaction)
```

* **Триггер:** Срабатывает при успешной отправке транзакции.
* **Действие:** Отображает пользователю информацию о транзакции.

#### Событие ошибки транзакции

Обработчик ошибок, возникающих при отправке транзакции.

```python
@tc.on_event(EventError.TRANSACTION)
async def transaction_error_event(error: TonConnectError, user_id: int) -> None:
    button_text, callback_data = "Try again", "main_menu"
    if isinstance(error, UserRejectsError):
        message_text = "You rejected the transaction."
    elif isinstance(error, RequestTimeoutError):
        message_text = "Transaction request timed out."
    else:
        message_text = f"Transaction error. Error: {error.message}"

    await error_window(user_id, message_text, button_text, callback_data)
```

* **Типы ошибок:**
    * **UserRejectsError:** Пользователь отклонил транзакцию.
    * **RequestTimeoutError:** Время ожидания запроса на транзакцию истекло.
    * **Другие ошибки:** Общие проблемы при отправке транзакции.
* **Действие:** Показывает сообщение об ошибке с возможностью вернуться в главное меню.

## Обработчики бота

Здесь показано, как различные функции бота взаимодействуют при обработке разных сценариев.

#### Обработчик команды /start

Обрабатывает команду /start для запуска процесса подключения кошелька или отображения действий при уже подключённом
кошельке.

```python
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
```

* **Инициализация:** Подготавливает коннектор для пользователя.
* **Ожидающие транзакции:** Отменяет активные транзакции, чтобы избежать конфликтов.
* **Статус подключения:** Определяет, нужно ли предложить подключение кошелька или показать доступные действия.

#### Обработчик callback-запросов

Обрабатывает различные callback-запросы, поступающие с inline-кнопок.

```python
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
        transfer_data = [
            TransferData(
                destination=connector.account.address,
                amount=0.000000001,
                body="Hello from tonutils!",
            ) for _ in range(4)
        ]
        rpc_request_id = await connector.send_batch_transfer(transfer_data)
        await send_transaction_window(callback_query.from_user.id)
        await state.update_data(rpc_request_id=rpc_request_id)

    await callback_query.answer()
```

* **Выбор кошелька (`app_wallet`):** Обновляет выбранный кошелёк и предлагает пользователю переподключиться.
* **Главное меню (`main_menu`):** Возвращает пользователя в окно с подключённым кошельком.
* **Подключить кошелёк (`connect_wallet`):** Запускает процесс подключения кошелька.
* **Отключить кошелёк (`disconnect_wallet`):** Запускает процесс отключения кошелька.
* **Отмена транзакции (`cancel_transaction`):** Отменяет ожидающую транзакцию и возвращает в окно подключённого
  кошелька.
* **Отправить транзакцию (`send_transaction`):** Инициирует отправку одной транзакции и предлагает пользователю
  подтвердить её.
* **Пакетная отправка транзакций (`send_batch_transaction`):** Инициирует отправку нескольких транзакций и предлагает
  подтверждение.

## Запуск бота

В завершение определите основную точку входа для запуска бота.

```python
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

* **Основная функция:** Запускает polling для получения входящих обновлений от Telegram.
* **Точка входа:** Обеспечивает запуск бота при прямом выполнении скрипта.

## Полный пример

Для справки приведён полный скрипт `bot.py`, объединяющий все описанные выше компоненты.

```python
# bot.py
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
from tonutils.wallet.data import TransferMessage

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
        transfer_data = [
            TransferMessage(
                destination=connector.account.address,
                amount=0.000000001,
                body="Hello from tonutils!",
            ) for _ in range(4)
        ]
        rpc_request_id = await connector.send_batch_transfer(transfer_data)
        await send_transaction_window(callback_query.from_user.id)
        await state.update_data(rpc_request_id=rpc_request_id)

    await callback_query.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

## Заключение

Следуя этому руководству, вы сможете успешно интегрировать TonConnect в свой Telegram-бот, обеспечив удобное подключение
кошельков и управление транзакциями.
