# Wallet Connection Cookbook

Welcome to the **Wallet Connection Cookbook**! This guide provides concise instructions to integrate and manage wallet
connections using the `TonConnect` from the `tonutils` library. Whether you're a beginner or an experienced developer,
this cookbook will help you implement wallet connectivity efficiently.

## Installation

Install the necessary Python packages using `pip`:

```bash
pip install tonutils aiofiles
```

## Configuration

Create a JSON file describing your application. This manifest is displayed in the wallet during connection.

    {
      "url": "<app-url>",                        // required
      "name": "<app-name>",                      // required
      "iconUrl": "<app-icon-url>",               // required
      "termsOfUseUrl": "<terms-of-use-url>",     // optional
      "privacyPolicyUrl": "<privacy-policy-url>" // optional
    }

**Note**: Ensure this file is publicly accessible via its URL.

## Initialize TonConnect

Set up the TonConnect instance with the manifest URL and [storage implementation](#storage-implementation).

```python
from storage import FileStorage

from tonutils.tonconnect import TonConnect

# URL of the publicly hosted JSON manifest of the application
TC_MANIFEST_URL = "https://your-domain.com/tonconnect-manifest.json"

# Initialize storage to save connected wallet data
TC_STORAGE = FileStorage("connection.json")

# Create an instance of TonConnect with the specified storage and manifest
tc = TonConnect(storage=TC_STORAGE, manifest_url=TC_MANIFEST_URL)
```

## Usage

### Event Handling

Handling events is essential for responding to wallet actions and errors. There are two primary methods to handle
events: using decorators and using context managers.

#### Using Decorators

Decorators associate event handlers with specific events. This method is straightforward and keeps your event handling
logic organized.

```python
@tc.on_event(Event.CONNECT)
async def on_wallet_connect(user_id: int, wallet: WalletInfo) -> None:
    wallet_address = wallet.account.address.to_str(is_bounceable=False)
    print(f"Wallet {wallet_address} connected to user {user_id}.")
```

#### Using Context Managers

Context managers provide a controlled environment for handling events, ensuring proper setup and teardown.

```python
async with connector.connect_wallet_context() as response:
    if isinstance(response, TonConnectError):
        print(f"Connection error: {response.message}")
    else:
        print(f"Connected wallet: {response.account.address.to_str(is_bounceable=False)}")
```

#### Passing Additional Parameters to Event Handlers

You can pass additional parameters to event handlers using `connector.add_event_kwargs`. This allows handlers to receive
extra information beyond the default parameters.

##### Example:

```python
connector.add_event_kwargs(event=Event.CONNECT, comment="Hello from tonutils!")
```

```python
@tc.on_event(Event.CONNECT)
async def on_wallet_connect(user_id: int, wallet: WalletInfo, comment: str) -> None:
    print(comment)
```

### Example Usage

Below is an example demonstrating connector initialization, event handling, and wallet management.

```python
import asyncio
import logging

from storage import FileStorage

from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import Event, EventError, WalletInfo
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError, RequestTimeoutError

# URL of the publicly hosted JSON manifest of the application
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"  # noqa

# Initialize storage to save connected wallet data
TC_STORAGE = FileStorage("connection.json")

# Create an instance of TonConnect with storage and manifest
tc = TonConnect(storage=TC_STORAGE, manifest_url=TC_MANIFEST_URL)


@tc.on_event(Event.CONNECT)
async def on_wallet_connect(user_id: int, wallet: WalletInfo) -> None:
    """
    Handler for successful wallet connection events.
    Processes all successful wallet connections and performs necessary actions.

    Available handler parameters:
    - user_id (int): User identifier
    - wallet (WalletInfo): Wallet information
    - Additional parameters can be passed using `connector.add_event_kwargs()`
      Example: `connector.add_event_kwargs(event=Event.CONNECT, comment="Hello from tonutils!")`
      In this example, `comment` is an additional parameter that will be passed to the handler.

    Wallet details can be obtained from the following attributes:
    - wallet.account (Account): Information about an account with an address, chain/network,
                                wallet state_init, and optional public key information.
    - wallet.ton_proof (TonProof): Verification details such as timestamp, domain information,
                                   payload, and a signature.
    - wallet.device (DeviceInfo): Information about a device associated with a wallet.
    """
    wallet_address = wallet.account.address.to_str(is_bounceable=False)
    print(f"Wallet {wallet_address} connected to user {user_id}.")


@tc.on_event(EventError.CONNECT)
async def on_wallet_connect_error(user_id: int, error: TonConnectError) -> None:
    """
    Handler for connection error events.
    Processes all errors that occur when connecting wallets.

    Available handler parameters:
    - user_id (int): User identifier
    - error (TonConnectError): Error information
    - Additional parameters can be passed using `connector.add_event_kwargs()`
      Example: `connector.add_event_kwargs(event=Event.CONNECT, comment="Hello from tonutils!")`
      In this example, `comment` is an additional parameter that will be passed to the handler.

    The type of error can be determined using isinstance:
    - UserRejectsError: User rejected the wallet connection.
    - RequestTimeoutError: Wallet connection timed out.
    """
    if isinstance(error, UserRejectsError):
        print(f"User {user_id} rejected the wallet connection.")
    elif isinstance(error, RequestTimeoutError):
        print(f"Connection request timed out for user {user_id}.")
    else:
        print(f"Connection error for user {user_id}: {error.message}")


@tc.on_event(Event.DISCONNECT)
async def on_wallet_disconnect(user_id: int, wallet: WalletInfo) -> None:
    """
    Handler for disconnected wallet events.
    Processes all successful wallet disconnections and performs necessary actions.

    Available handler parameters:
    - user_id (int): User identifier
    - wallet (WalletInfo): Wallet information
    - Additional parameters can be passed using `connector.add_event_kwargs()`
      Example: `connector.add_event_kwargs(event=Event.DISCONNECT, comment="Hello from tonutils!")`
      In this example, `comment` is an additional parameter that will be passed to the handler.
    """
    wallet_address = wallet.account.address.to_str(is_bounceable=False)
    print(f"Wallet {wallet_address} disconnected from user {user_id}.")


@tc.on_event(EventError.DISCONNECT)
async def on_wallet_disconnect_error(user_id: int, error: TonConnectError) -> None:
    """
    Handler for disconnected wallet events.
    Processes all successful wallet disconnections and performs necessary actions.

    Available handler parameters:
    - user_id (int): User identifier
    - error (TonConnectError): Error information
    - Additional parameters can be passed using `connector.add_event_kwargs()`
      Example: `connector.add_event_kwargs(event=Event.DISCONNECT, comment="Hello from tonutils!")`
      In this example, `comment` is an additional parameter that will be passed to the handler.
    """
    if isinstance(error, RequestTimeoutError):
        print(f"Disconnect request timed out for user {user_id}.")
    else:
        print(f"Disconnect error for user {user_id}: {error.message}")


async def main() -> None:
    user_id = 12345  # Example user ID

    # Initialize the connector for the user
    connector = await tc.init_connector(user_id)

    if not connector.connected:
        wallets = await tc.get_wallets()
        selected_wallet = wallets[1]  # Example: Tonkeeper
        connect_url = await connector.connect_wallet(selected_wallet)
        print(f"Connect your wallet here:\n{connect_url}")

        # Add additional parameters to event handlers
        connector.add_event_kwargs(event=Event.TRANSACTION, some_param="foo")

        print("Waiting for wallet connection...")
        async with connector.connect_wallet_context() as response:
            if isinstance(response, TonConnectError):
                print(f"Connection error: {response.message}")
            else:
                print(f"Connected wallet: {response.account.address.to_str(is_bounceable=False)}")
    else:
        wallet_address = connector.account.address.to_str(is_bounceable=False)
        print(f"Wallet already connected: {wallet_address}")

        user_input = input("Do you want to disconnect the wallet? (y/n): ").strip().lower()
        if user_input == 'y':
            await connector.disconnect_wallet()
            print("Wallet successfully disconnected.")
        else:
            print("Wallet remains connected.")

    await tc.close_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        asyncio.run(tc.close_all())
```

## Storage Implementation

The `FileStorage` class manages persistent storage of connection data using a JSON file.

```python
import json
import os
from asyncio import Lock
from typing import Optional, Dict

import aiofiles

from tonutils.tonconnect import IStorage


class FileStorage(IStorage):

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = Lock()

        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({}, f)  # type: ignore

    async def _read_data(self) -> Dict[str, str]:
        async with self.lock:
            async with aiofiles.open(self.file_path, 'r') as f:
                content = await f.read()
                if content:
                    return json.loads(content)
                return {}

    async def _write_data(self, data: Dict[str, str]) -> None:
        async with self.lock:
            async with aiofiles.open(self.file_path, 'w') as f:
                await f.write(json.dumps(data, indent=4))

    async def set_item(self, key: str, value: str) -> None:
        data = await self._read_data()
        data[key] = value
        await self._write_data(data)

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        data = await self._read_data()
        return data.get(key, default_value)

    async def remove_item(self, key: str) -> None:
        data = await self._read_data()
        if key in data:
            del data[key]
            await self._write_data(data)
```

## Ton Proof Verification

To confirm that a user truly owns the connected wallet, you can use the Ton Proof mechanism. It verifies both the user's
address and the validity of their signed payload.
This is especially useful for authenticating users before giving access to personalized backend data.

* A full example is available in
  the [check_proof](https://github.com/nessshon/tonutils/tree/main/examples/tonconnect/wallet_connection/check_proof.py)
  file.
* Learn more: Verifying signed-in users on
  backend [TON Docs](https://docs.ton.org/v3/guidelines/ton-connect/guidelines/verifying-signed-in-users)

## Conclusion

By following this cookbook, you can successfully integrate TonConnect into your script enabling seamless wallet
connections.