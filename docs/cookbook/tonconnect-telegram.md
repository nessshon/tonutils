## Introduction

This guide demonstrates how to integrate TON Connect into a Telegram bot using `tonutils` — a Python SDK designed for seamless interaction with TON.

The bot provides the following functionality:

- Connect a wallet via QR code or link
- Sign arbitrary data
- Send transactions

The implementation follows production best practices: persistent session storage, asynchronous architecture, anti-spam protection, and a minimal UI using inline buttons.

!!! tip
    Before getting started, it's recommended to review the documentation [Cookbook: TON Connect Integration](tonconnect-integration.md)

## Setup

Before getting started, complete the following steps.

### Creating a Telegram Bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram.
2. Send the `/newbot` command and follow the prompts.
3. Save the bot token.

### Create TonConnect Manifest

Create a JSON file describing your application. This manifest is displayed in the wallet during connection.

  ```json
  {
    "url": "<app-url>",                        // required
    "name": "<app-name>",                      // required
    "iconUrl": "<app-icon-url>",               // required
    "termsOfUseUrl": "<terms-of-use-url>",     // optional
    "privacyPolicyUrl": "<privacy-policy-url>" // optional
  }
  ```

!!! note
    Ensure this file is publicly accessible via its URL.

Refer to the official [manifest documentation](https://docs.ton.org/v3/guidelines/ton-connect/guidelines/creating-manifest) for detailed specifications.

## Installing Dependencies

Create a `requirements.txt` file with the following contents:

```
--8<-- "examples/tonconnect/telegram_bot/requirements.txt"
```

Install all dependencies by running:

```bash
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file in the root directory of your project and define the following variables:

```env
BOT_TOKEN=your_bot_token
REDIS_DSN=redis://localhost:6379/0
TC_MANIFEST=https://your-domain.com/manifest.json
```

Description of variables:

* `BOT_TOKEN` — Telegram bot token obtained from [@BotFather](https://t.me/BotFather).
* `REDIS_DSN` — Redis connection string used to store sessions and states.
* `TC_MANIFEST` — HTTPS URL pointing to the publicly available TON Connect manifest.


## Project Structure

```
├── .env
├── requirements.txt
└── src/
    ├── utils/
    │   ├── __init__.py
    │   ├── keyboards.py
    │   ├── models.py
    │   ├── storage.py
    │   └── windows.py
    ├── __init__.py
    ├── __main__.py
    ├── events.py
    ├── handlers.py
    ├── middlewares.py
    └── session_manager.py
```

## Implementation

The project is split into separate modules, each handling a specific responsibility. Let's go through them step by step.

### Configuration

**File:** `src/utils/models.py`

This module is responsible for:

- Loading configuration values from the `.env` file.
- Creating the `Context` class that holds essential dependencies.

#### Context contents

- `bot: Bot` — instance of the Telegram bot (`aiogram`).
- `state: FSMContext` — finite-state machine context per user.
- `tc: TonConnect` — main interface to interact with TON wallets.
- `connector: Connector` — user-specific connection session.

#### Usage

- At startup, `Config.load()` is called to load environment variables.
- The middleware creates a `Context` instance and injects it into all handlers for convenient access to shared resources.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/utils/models.py"
```

</details>

### Session Storage

**File:** `src/utils/storage.py`

In the web version of TON Connect, wallet sessions are stored using `localStorage`. In a Python server environment, you need to implement a custom session storage solution.

This project uses Redis, where TON Connect sessions are stored and retrieved using the user's Telegram ID as the key.

#### Module responsibilities

- Store TON Connect session data by Telegram ID.
- Retrieve session data when the user reconnects.
- Delete session data upon disconnect or cleanup.

This approach ensures reliable persistence and recovery of user session state.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/utils/storage.py"
```

</details>

### Message Cleanup

**File:** `src/utils/__init__.py`

This module ensures that the user's previous message is deleted before a new one is sent. It prevents clutter in the chat and helps maintain a clean, minimal user interface.

#### How it works

- The user's FSM context stores the `message_id` of the last message sent by the bot.
- Before sending a new message, the bot tries to delete the previous one.
- After sending, it stores the new `message_id` for the next cleanup cycle.

This is especially useful for bots with dynamic inline UIs that refresh often.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/utils/__init__.py"
```

</details>

### Keyboards

**File:** `src/utils/keyboards.py`

This module is responsible for generating inline keyboards for user interaction. It ensures fast navigation and a clean, responsive interface.

#### Main keyboard types

- **Wallet connection** — a list of available wallets with connect buttons.
- **Request confirmation** — buttons for opening the wallet or canceling the current request.
- **Main action menu** — send transaction, batch transfer, sign data, disconnect.
- **Signature format selection** — choose between text, binary, or `cell`.
- **Back to menu** — return to the main screen.

The keyboards are dynamically adjusted based on user context and current workflow.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/utils/keyboards.py"
```

</details>

### UI Windows

**File:** `src/utils/windows.py`

This module handles communication with the user via Telegram messages and inline keyboards. It implements logical UI “screens” that represent different interaction states.

#### Key responsibilities

- **Wallet connection screen** — shows the list of wallets, generates `ton_proof`, builds a connect link and QR code.
- **Main menu** — displays the connected wallet address and offers actions: send, sign, disconnect.
- **Request confirmation** — prompts the user to confirm the action inside their wallet app.
- **Result display** — shows transaction hashes, signature data, and verification results.
- **Error handling** — informs the user of failures and offers options to retry or return.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/utils/windows.py"
```

</details>

### Session Cleanup

**File:** `src/session_manager.py`

This module implements a background task that monitors user activity and closes inactive TON Connect SSE sessions to reduce resource usage.

#### Key mechanisms

- User last activity timestamps are stored in Redis using a sorted set (`ZSET`).
- The cleaner periodically scans for users who have been inactive for longer than `session_lifetime`.
- For each inactive user, `pause_sse()` is called on their connector to suspend the open connection.
- After pausing, the user record is removed from Redis.

#### Configuration parameters

- `session_lifetime` — maximum allowed inactivity duration (default: 1 hour).
- `check_interval` — interval between cleanup iterations (default: 10 minutes).
- `redis_key` — Redis key used to track last activity timestamps.

This mechanism is essential in production environments where open connections must be optimized for scalability.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/session_manager.py"
```

</details>

### Middleware

**File:** `src/middlewares.py`

This module defines two essential middlewares for the Telegram bot:

#### ContextMiddleware

- Creates a `Context` object for each incoming update.
- It also updates the user's last activity timestamp, allowing accurate session tracking and cleanup.

#### ThrottlingMiddleware

- A simple anti-spam mechanism.
- Uses a TTL-based cache to block repeated requests from the same user within a short interval.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/middlewares.py"
```

</details>

### Event Handling

**File:** `src/events.py`

This module registers and handles all TON Connect events, along with associated errors.

#### Main event types

- **Wallet connection (`CONNECT`)**
    - Verifies `ton_proof` to confirm wallet ownership.
    - On success, displays the main action menu.
    - On failure, disconnects and prompts the user to retry.

- **Connection errors**
    - Handles timeouts and request rejections.
    - Notifies the user and provides an option to reconnect.

- **Wallet disconnection (`DISCONNECT`)**
    - Handles both manual and forced disconnects (e.g. invalid proof).
    - Prompts the user to reconnect.

- **Disconnection errors**
    - Notifies the user without interrupting the session flow.

- **Transaction (`TRANSACTION`)**
    - Displays transaction hash on success.
    - Shows error message with options to retry or return to menu on failure.

- **Sign data (`SIGN_DATA`)**
    - Shows signature results and verification status.
    - Informs the user of any issues during the signing process.

All event handlers are registered using the `register_event` method of the `TonConnect` instance.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/events.py"
```

</details>

### Telegram Handlers

**File:** `src/handlers.py`

This module contains Telegram handlers for user interactions via commands and inline buttons.

#### Main responsibilities

- **Handling the `/start` command**
    - If no wallet is connected — initiates wallet selection and connection flow.
    - If already connected — displays the main menu with available actions.

- **Handling inline callback queries**
    - Selecting a wallet and starting the connection process.
    - Navigating through menus: main menu, connect, disconnect.
    - Cancelling active requests: transactions or signing.
    - Sending a single transaction.
    - Sending a batch transaction.
    - Requesting data signing.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/handlers.py"
```

</details>

### Entry Point

**File:** `src/__main__.py`

This module serves as the glue for the entire application and initiates the bot lifecycle.

#### Main responsibilities

- Loads configuration from `.env` using `Config.load()`.
- Establishes Redis connections:
    - for FSM state storage,
    - for TonConnect session persistence.
- Initializes key components `Bot`, `TonConnect`, `Dispatcher`:
- Registers:
    - Telegram command and callback handlers,
    - TonConnect event listeners,
    - middlewares.
- Starts the background `TonConnectSessionManager` task to suspend inactive sessions.
- Launches polling to process incoming Telegram updates.

<details>
<summary>Code example</summary>

```python
--8<-- "examples/tonconnect/telegram_bot/src/__main__.py"
```

</details>

### Running the Bot

* Ensure the `.env` file is present in the project root with all required environment variables.
* Make sure the Redis server is running and reachable at the `REDIS_DSN` address.
* Start the bot using:

    ```bash
    python -m src
    ```

## Conclusion

This bot provides a solid and extensible foundation for integrating TON Connect into Telegram. It implements essential functionality for wallet connection, transaction sending, and data signing, while also supporting session persistence and SSE-based resource optimization.
The modular architecture makes it easy to adapt and extend for various use cases.

Full source code is available at: [tonconnect-demo-bot](https://github.com/nessshon/tonutils/blob/main/examples/tonconnect/telegram_bot)

## See also

* [TON Connect Documentation and Specifications](https://github.com/ton-blockchain/ton-connect)
* [tonutils TON Connect Documentation](https://nessshon.github.io/tonutils/cookbook/tonconnect-integration/)
* [aiogram Documentation](https://docs.aiogram.dev/)
