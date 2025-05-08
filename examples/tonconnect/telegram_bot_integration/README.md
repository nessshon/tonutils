# Telegram Bot Integration

This guide provides step-by-step instructions to integrate and
manage wallet connections and transactions within a Telegram Bot using the `TonConnect` from the `tonutils` library.
Whether you're a beginner or an experienced developer, this cookbook will help you implement wallet connectivity and
transaction functionalities efficiently within your Telegram Bot.

## Installation

Install the necessary Python packages using `pip`:

```bash
pip install tonutils aiogram redis
```

## Structure

Organize your project files as follows:

```
telegram-tonconnect-bot/
├── bot.py
├── storage.py
```

* **bot.py**: Main bot script containing bot logic.
* **storage.py**: Custom [storage implementation](#storage-implementation) for TonConnect.

## Configuration

### Create TonConnect Manifest

Create a JSON file describing your application. This manifest is displayed in the wallet during connection.

    {
      "url": "<app-url>",                        // required
      "name": "<app-name>",                      // required
      "iconUrl": "<app-icon-url>",               // required
      "termsOfUseUrl": "<terms-of-use-url>",     // optional
      "privacyPolicyUrl": "<privacy-policy-url>" // optional
    }

!!! note
Ensure this file is publicly accessible via its URL.

### Storage Implementation

TonConnect requires a storage system to manage its data. Here, we implement a Redis-based storage class.

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

### Initialization

Create a Python script and set up the initial configuration.

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
from tonutils.wallet.data import TransferData

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
tc = TonConnect(storage=TCRedisStorage(redis), manifest_url=TC_MANIFEST_URL, wallets_fallback_file_path="./wallets.json")
```

* **Redis Initialization**: Establishes a connection to the Redis server.
* **Dispatcher & Bot Initialization**: Sets up the dispatcher with Redis storage and initializes the bot.
* **TonConnect Initialization**: Sets up TonConnect with custom Redis storage and the manifest URL.

## Bot Helper Functions

### Keyboards

Functions to create various inline keyboards used in the bot.

#### Connect Wallet Markup

Creates an inline keyboard for selecting and connecting wallets.

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

* **Wallet Buttons:** Lists available wallets, highlighting the selected one.
* **Connect Button:** Provides a direct link to connect the selected wallet.
* **Layout:** Uses InlineKeyboardBuilder to organize buttons neatly.

#### Confirm Transaction Markup

Creates an inline keyboard for confirming or canceling a transaction.

```python
def _confirm_transaction_markup(url: str, wallet_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Open {wallet_name}", url=url)],
            [InlineKeyboardButton(text="Cancel", callback_data="cancel_transaction")],
        ]
    )
```

* **Open Wallet Button:** Directs the user to their wallet for transaction confirmation.
* **Cancel Button:** Allows the user to cancel the pending transaction.

#### Choose Action Markup

Creates an inline keyboard for selecting actions after wallet connection.

```python
def _choose_action_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Send transaction", callback_data="send_transaction"))
    builder.row(InlineKeyboardButton(text="Send batch transaction", callback_data="send_batch_transaction"))
    builder.row(InlineKeyboardButton(text="Disconnect wallet", callback_data="disconnect_wallet"))

    return builder.as_markup()
```

* **Actions:** Users can choose to send a single transaction, send multiple transactions in a batch, or disconnect their
  wallet.

#### Go to Main Menu Markup

Creates an inline keyboard to navigate back to the main menu.

```python
def _go_to_main_menu_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Main menu", callback_data="main_menu"))

    return builder.as_markup()
```

* **Main Menu Button:** Provides a way for users to return to the primary interface.

### Windows

Define various user interface windows that respond to user interactions and TonConnect events.

#### Connect Wallet Window

Displays the wallet connection interface to the user.

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

* **Connector Initialization:** Prepares the TonConnect connector for the user.
* **Wallet Selection:** Retrieves available wallets and selects the preferred one.
* **QR Code Generation:** Generates a QR code URL for wallet connection.
* **User Prompt:** Sends a message prompting the user to connect their wallet with the appropriate inline keyboard.

#### Wallet Connected Window

Displays the connected wallet information and available actions.

```python
async def wallet_connected_window(user_id: int) -> None:
    connector = await tc.init_connector(user_id)
    wallet_address = connector.wallet.account.address.to_str(is_bounceable=False)

    reply_markup = _choose_action_markup()
    text = f"Connected wallet:\n{hcode(wallet_address)}\n\nChoose an action:"

    message = await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)
```

* **Wallet Information:** Shows the connected wallet's address.
* **Available Actions:** Presents options to send transactions, send batch transactions, or disconnect the wallet.

#### Send Transaction Window

Prompts the user to confirm the transaction in their wallet.

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

* **User Prompt:** Instructs the user to confirm the transaction within their wallet.
* **Confirmation Options:** Provides buttons to open the wallet or cancel the transaction.

#### Transaction Sent Window

Displays the transaction details after a successful send.

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

* **Transaction Details:** Provides the transaction hash and BoC (Bag of Cells) for reference.
* **Navigation:** Offers a button to return to the main menu.

#### Error Window

Displays error messages with an option to retry or go back.

```python
async def error_window(user_id: int, message_text: str, button_text: str, callback_data: str) -> None:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    reply_markup = builder.as_markup()

    message = await bot.send_message(chat_id=user_id, text=message_text, reply_markup=reply_markup)
    await delete_last_message(user_id, message.message_id)
```

* **Error Message:** Communicates the issue to the user.
* **Retry Option:** Provides a button to attempt the failed action again or navigate elsewhere.

### Utils

Function to delete the last message sent to the user to keep the chat clean.

```python
async def delete_last_message(user_id: int, message_id: int) -> None:
    state = dp.fsm.resolve_context(bot, user_id, user_id)
    last_message_id = (await state.get_data()).get("last_message_id")

    if last_message_id is not None:
        with suppress(Exception):
            await bot.delete_message(chat_id=user_id, message_id=last_message_id)

    await state.update_data(last_message_id=message_id)
```

* **Purpose**: Ensures that only the latest message is visible to the user, enhancing the user experience by reducing
  clutter.
* **Functionality**:
    * Retrieves the last message ID from the user's state data.
    * Attempts to delete the last message if it exists.
    * Updates the state with the new message ID.

## TonConnect handlers

TonConnect utilizes event-driven architecture to handle various wallet-related actions. This section outlines how to
handle these events within your bot.

#### Connect Event

Handler for successful wallet connection events.

```python
@tc.on_event(Event.CONNECT)
async def connect_event(user_id: int) -> None:
    await wallet_connected_window(user_id)
```

* **Trigger:** When a wallet is successfully connected.
* **Action:** Displays the connected wallet information and available actions to the user.

#### Connect Error Event

Handler for wallet connection errors.

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

* **Error Types:**
    * **UserRejectsError:** User declined the connection.
    * **RequestTimeoutError:** Connection request timed out.
    * **Other errors:** Generic connection issues.
* **Action:** Displays an error message with an option to retry.

#### Disconnect Event

Handler for successful wallet disconnection events.

```python
@tc.on_event(Event.DISCONNECT)
async def disconnect_event(user_id: int) -> None:
    state = dp.fsm.resolve_context(bot, user_id, user_id)
    await connect_wallet_window(state, user_id)
```

* **Trigger:** When a wallet is successfully disconnected.
* **Action:** Prompts the user to reconnect their wallet.

#### Disconnect Error Event

Handler for wallet disconnection errors.

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

* **Error Types:**
    * **UserRejectsError:** User declined the disconnection.
    * **RequestTimeoutError:** Disconnection request timed out.
    * **Other errors:** Generic disconnection issues.
* **Action:** Displays an error message with an option to retry.

#### Transaction Event

Handler for successful transaction events.

```python
@tc.on_event(Event.TRANSACTION)
async def transaction_event(user_id: int, transaction: SendTransactionResponse) -> None:
    await transaction_sent_window(user_id, transaction)
```

* **Trigger:** When a transaction is successfully sent.
* **Action:** Displays transaction details to the user

#### Transaction Error Event

Handler for transaction errors.

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

* **Error Types:**
    * **UserRejectsError:** User declined the transaction.
    * **RequestTimeoutError:** Transaction request timed out.
    * **Other errors:** Generic transaction issues.
* **Action:** Displays an error message with an option to return to the main menu.

## Bot handlers

Here's how the bot's functionalities come together in handling various scenarios.

#### Start Command Handler

Handles the /start command to initiate the wallet connection process or display connected wallet actions.

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

* **Initialization:** Prepares the connector for the user.
* **Pending Transactions:** Cancels any ongoing transactions to prevent conflicts.
* **Connection Status:** Determines whether to prompt for wallet connection or display available actions.

#### Callback Query Handler

Handles various callback queries from inline buttons.

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

* **Wallet Selection (`app_wallet`:):** Updates the selected wallet and prompts the user to reconnect.
* **Main Menu (`main_menu`):** Returns to the wallet connected window.
* **Connect Wallet (`connect_wallet`):** Initiates the wallet connection process.
* **Disconnect Wallet (`disconnect_wallet`):** Initiates the wallet disconnection process.
* **Cancel Transaction (`cancel_transaction`):** Cancels any pending transactions and returns to the connected wallet
  window.
* **Send Transaction (`send_transaction`):** Initiates a single transaction and prompts the user to confirm.
* **Send Batch Transaction (`send_batch_transaction`):** Initiates multiple transactions in a batch and prompts the user
  to confirm.

## Running the Bot

Finally, define the main entry point to start the bot.

```python
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

* **Main Function:** Starts polling to listen for incoming updates from Telegram.
* **Entry Point:** Ensures the bot starts when the script is executed directly.

## Complete Example

For reference, here's the complete bot.py script integrating all the components discussed above.

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
from tonutils.wallet.data import TransferData

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


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

Conclusion
----------

By following this cookbook, you can successfully integrate TonConnect into your Telegram Bot, enabling seamless wallet
connections and transaction management.
