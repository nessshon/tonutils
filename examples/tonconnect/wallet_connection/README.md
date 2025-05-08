This guide provides concise instructions to integrate and manage wallet
connections using the `TonConnect` from the `tonutils` library. Whether you're a beginner or an experienced developer,
this cookbook will help you implement wallet connectivity efficiently.

## Installation

Install the necessary Python packages using `pip`:

```bash
pip install tonutils aiofiles
```

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

### Initialize TonConnect

Set up the TonConnect instance with the manifest URL and [storage implementation](#storage-implementation).

```python
from storage import FileStorage

from tonutils.tonconnect import TonConnect

# URL of the publicly hosted JSON manifest of the application
# For detailed information: https://github.com/ton-blockchain/ton-connect/blob/main/requests-responses.md#app-manifest
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"

# Initialize storage to save connected wallet data
# In this example, FileStorage from storage.py is used
TC_STORAGE = FileStorage("connection.json")

# Create an instance of TonConnect with the specified storage and manifest
tc = TonConnect(storage=TC_STORAGE, manifest_url=TC_MANIFEST_URL, wallets_fallback_file_path="./wallets.json")
```

## Event Handling

Handling events is essential for responding to wallet actions and errors. There are two primary methods to handle
events: using decorators and using context managers.

### Using Decorators

Decorators associate event handlers with specific events. This method is straightforward and keeps your event handling
logic organized.

```python
@tc.on_event(Event.CONNECT)
async def on_wallet_connect(user_id: int, wallet: WalletInfo) -> None:
    wallet_address = wallet.account.address.to_str(is_bounceable=False)
    print(f"Wallet {wallet_address} connected to user {user_id}.")
```

### Using Context Managers

Context managers provide a controlled environment for handling events, ensuring proper setup and teardown.

```python
async with connector.connect_wallet_context() as response:
    if isinstance(response, TonConnectError):
        print(f"Connection error: {response.message}")
    else:
        print(f"Connected wallet: {response.account.address.to_str(is_bounceable=False)}")
```

### Passing Additional Parameters

In some cases, you may want to provide custom data or context to your event handlers — for example, adding tags, notes,
or extra flags.

You can achieve this by using the `connector.add_event_kwargs` method, which attaches additional keyword arguments that
will be passed into the handler alongside the default parameters.

**Step 1: Add Custom Parameters**

Call `add_event_kwargs` before triggering or waiting on an event:

```python
connector.add_event_kwargs(
    event=Event.CONNECT,
    comment="Hello from tonutils!",
)
```

**Step 2: Update the Event Handler to Receive Them**

Define the handler to accept these extra parameters:

```python
@tc.on_event(Event.CONNECT)
async def on_wallet_connect(user_id: int, wallet: WalletInfo, comment: str) -> None:
    print(f"Comment: {comment}")
```

**Key Points:**

* You can attach multiple parameters (any keyword argument).
* The handler function must include matching parameter names.
* This mechanism works for **all** supported events (`CONNECT`, `DISCONNECT`, `TRANSACTION`, etc.).

## Complete Example

Below is an example demonstrating connector initialization, event handling, and wallet management.

```python
import json
import os
from asyncio import Lock
from typing import Dict, Optional

import aiofiles

from tonutils.tonconnect import TonConnect, IStorage
from tonutils.tonconnect.models import Event, EventError, WalletInfo
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError, RequestTimeoutError


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


# URL of the publicly hosted JSON manifest of the application
# For detailed information: https://github.com/ton-blockchain/ton-connect/blob/main/requests-responses.md#app-manifest
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"  # noqa

# Initialize storage to save connected wallet data
# In this example, FileStorage from storage.py is used
TC_STORAGE = FileStorage("connection.json")

# Create an instance of TonConnect with the specified storage and manifest
tc = TonConnect(storage=TC_STORAGE, manifest_url=TC_MANIFEST_URL, wallets_fallback_file_path="./wallets.json")


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
    print(f"[CONNECT EVENT] Wallet {wallet_address} connected to user {user_id}.")


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
        print(f"[CONNECT ERROR] User {user_id} rejected the wallet connection.")
    elif isinstance(error, RequestTimeoutError):
        print(f"[CONNECT ERROR] Connection request timed out for user {user_id}.")
    else:
        print(f"[CONNECT ERROR] Connection error for user {user_id}. Error: {error.message}")


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
    print(f"[DISCONNECT EVENT] Wallet {wallet_address} disconnected from user {user_id}.")


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
        print(f"[DISCONNECT ERROR] Disconnect request timed out for user {user_id}.")
    else:
        print(f"[DISCONNECT ERROR] Disconnect error for user {user_id}. Error: {error.message}")


async def main() -> None:
    user_id = 12345  # Example user ID

    # Initialize the connector for the user
    connector = await tc.init_connector(user_id)

    # Check if the wallet is already connected
    if not connector.connected:
        # Get all available wallets
        wallets = await tc.get_wallets()

        # As an example, we will select the wallet with index 1 (Tonkeeper)
        selected_wallet = wallets[1]
        connect_url = await connector.connect_wallet(selected_wallet)
        print(f"Please connect your wallet by visiting the following URL:\n{connect_url}")

        # Add additional parameters to be passed to event handlers
        connector.add_event_kwargs(event=Event.TRANSACTION, comment="Hello from tonutils!")
        # After this, you can use:
        """
        @tc.on_event(Event.CONNECT)
        async def on_wallet_connect(user_id: int, wallet: WalletInfo, comment: str) -> None:...
        """

        print("Waiting for wallet connection...")
        async with connector.connect_wallet_context() as response:
            if isinstance(response, TonConnectError):
                print(f"Connection error: {response.message}")
            else:
                print(f"Connected wallet: {response.account.address.to_str(is_bounceable=False)}")

    else:
        wallet_address = connector.account.address.to_str(is_bounceable=False)
        print(f"Wallet already connected: {wallet_address}")

        # Prompt the user to disconnect the wallet
        user_input = input("Do you want to disconnect the wallet? (y/n): ").strip().lower()

        if user_input == 'y':
            # Disconnect the wallet
            await connector.disconnect_wallet()
            print("Wallet successfully disconnected.")
        else:
            print("Wallet remains connected.")

    # Close all TonConnect connections
    await tc.close_all()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Ensure all connections are closed in case of interruption
        asyncio.run(tc.close_all())
```

## Ton Proof Example

To confirm ownership of a wallet, use Ton Proof to validate signed payloads.

```python
from storage import FileStorage
from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.utils.exceptions import TonConnectError
from tonutils.tonconnect.utils.proof import generate_proof_payload, verify_proof_payload

# URL of the publicly hosted JSON manifest of the application
# For detailed information: https://github.com/ton-blockchain/ton-connect/blob/main/requests-responses.md#app-manifest
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"

# Initialize storage to save connected wallet data
# In this example, FileStorage from storage.py is used
TC_STORAGE = FileStorage("connection.json")

# Create an instance of TonConnect with the specified storage and manifest
tc = TonConnect(storage=TC_STORAGE, manifest_url=TC_MANIFEST_URL, wallets_fallback_file_path="./wallets.json")


async def main() -> None:
    user_id = 1  # Example user ID

    # Initialize the connector for the user
    connector = await tc.init_connector(user_id)

    # Generate the proof payload
    proof_payload = generate_proof_payload()

    # Check if the wallet is already connected
    if not connector.connected:
        # Get all available wallets
        wallets = await tc.get_wallets()

        # As an example, we will select the wallet with index 1 (Tonkeeper)
        selected_wallet = wallets[1]
        connect_url = await connector.connect_wallet(selected_wallet, ton_proof=proof_payload)
        print(f"Please connect your wallet by visiting the following URL:\n{connect_url}")

        print("Waiting for wallet connection...")
        async with connector.connect_wallet_context() as response:
            if isinstance(response, TonConnectError):
                print(f"Connection error: {response.message}")
            else:
                if verify_proof_payload(proof_payload, connector.wallet):
                    print(f"Connected wallet: {response.account.address.to_str(is_bounceable=False)}")
                else:
                    await connector.disconnect_wallet()
                    print("Proof verification failed.")

    else:
        wallet_address = connector.account.address.to_str(is_bounceable=False)
        print(f"Wallet already connected: {wallet_address}")

        # Prompt the user to disconnect the wallet
        user_input = input("Do you want to disconnect the wallet? (y/n): ").strip().lower()

        if user_input == 'y':
            # Disconnect the wallet
            await connector.disconnect_wallet()
            print("Wallet successfully disconnected.")
        else:
            print("Wallet remains connected.")

    # Close all TonConnect connections
    await tc.close_all()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Ensure all connections are closed in case of interruption
        asyncio.run(tc.close_all())
```

Conclusion
----------

By following this cookbook, you can successfully integrate TonConnect into your script enabling seamless wallet
connections.
