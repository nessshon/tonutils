This guide provides step-by-step instructions for integrating and
managing transaction sending using the `TonConnect` from the `tonutils` library. Whether you're a beginner or an
experienced developer, this guide will help you implement transaction functionality efficiently.

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

Handling events is essential for responding to transaction actions and errors. There are two primary methods to handle
events: using decorators and using context managers.

### Using Decorators

Decorators associate event handlers with specific events. This method is straightforward and keeps your event handling
logic organized.

```python
@tc.on_event(Event.TRANSACTION)
async def on_transaction(transaction: SendTransactionResponse) -> None:
    print(f"[Transaction SENT] Transaction successfully sent. Message hash: {transaction.normalized_hash}")
```

### Using Context Managers

Context managers provide a controlled environment for handling events, ensuring proper setup and teardown.

```python
async with connector.pending_transaction_context(rpc_request_id) as response:
    if isinstance(response, TonConnectError):
        print(f"Error sending transaction: {response.message}")
    else:
        print(f"Transaction successful! Hash: {response.normalized_hash}")
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
    event=Event.TRANSACTION,
    comment="Hello from tonutils!",
)
```

**Step 2: Update the Event Handler to Receive Them**

Define the handler to accept these extra parameters:

```python
@tc.on_event(Event.TRANSACTION)
async def on_transaction(user_id: int, transaction: SendTransactionResponse, comment: str) -> None:
    print(f"Comment: {comment}")
```

**Key Points:**

* You can attach multiple parameters (any keyword arguments).
* The handler function must include matching parameter names.
* This mechanism works for **all** supported events (`CONNECT`, `DISCONNECT`, `TRANSACTION`, etc.).

## Sending Transactions

### Sending a Single Transaction

To send a single transaction, use the `send_transfer` method. This method sends a transaction to a specified destination
with a certain amount and an optional message body.

```python
rpc_request_id = await connector.send_transfer(
    destination=connector.account.address,
    amount=0.000000001,  # Amount in TON
    body="Hello from tonutils!",
)
print("Request to send one transaction has been sent.")
```

### Sending a Batch of Transactions

To send multiple messages, use the `send_batch_transfer` method.

```python
# Get the maximum number of messages supported
max_messages = connector.get_max_supported_messages()
print(f"Maximum number of messages: {max_messages}. Sending {max_messages} transactions...")

rpc_request_id = await connector.send_batch_transfer(
    data_list=[
        TransferData(
            destination=connector.account.address,
            amount=0.000000001,
            body="Hello from tonutils!",
        ) for _ in range(max_messages)  # Create the maximum number of messages
    ]
)
print("Request to send a batch of transactions has been sent.")
```

### Handling Transaction Status

After sending a transaction, you may want to check its status to determine if it has been confirmed by the user in the
wallet.

```python
# Get the transaction status (whether it has been confirmed by the user in the wallet)
is_pending = connector.is_transaction_pending(rpc_request_id)
print(f"Transaction is pending confirmation: {is_pending}")

# Use a context manager to get the transaction result by rpc_request_id
async with connector.pending_transaction_context(rpc_request_id) as response:
    if isinstance(response, TonConnectError):
        print(f"Error sending transaction: {response.message}")
    else:
        print(f"Transaction successful! Hash: {response.normalized_hash}")
```

## Complete Example

Below is a comprehensive example demonstrating connector initialization, event handling, sending transactions, and
wallet management.

```python
import asyncio
import json
import os
from asyncio import Lock
from typing import Dict, Optional

import aiofiles

from tonutils.tonconnect import TonConnect, IStorage
from tonutils.tonconnect.models import Event, EventError, SendTransactionResponse
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError, RequestTimeoutError
from tonutils.wallet.data import TransferData


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
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"

# Initialize storage to save connected wallet data
# In this example, FileStorage from storage.py is used
TC_STORAGE = FileStorage("connection.json")

# Create an instance of TonConnect with the specified storage and manifest
tc = TonConnect(storage=TC_STORAGE, manifest_url=TC_MANIFEST_URL, wallets_fallback_file_path="./wallets.json")


@tc.on_event(Event.TRANSACTION)
async def on_transaction(transaction: SendTransactionResponse) -> None:
    """
    Handler for successful transaction events.
    Processes all successful transactions and performs necessary actions.

    Available handler parameters:
    - user_id (int): User identifier
    - transaction (SendTransactionResponse): Transaction information
    - rpc_request_id (int): Transaction request identifier
    - Additional parameters can be passed using `connector.add_event_kwargs(...)`
      Example: `connector.add_event_kwargs(event=Event.TRANSACTION, comment="Hello from tonutils!")`
      In this example, `comment` is an additional parameter that will be passed to the handler.

    Transaction details can be obtained from the following attributes:
    - transaction.boc (str): BoC
    - transaction.normalized_hash (str): Message hash
    - transaction.cell (Cell): Transaction Cell
    """
    print(f"[Transaction SENT] Transaction successfully sent. Message hash: {transaction.normalized_hash}")


@tc.on_event(EventError.TRANSACTION)
async def on_transaction_error(error: TonConnectError) -> None:
    """
    Handler for transaction error events.
    Processes all errors that occur when sending transactions.

    Available handler parameters:
    - user_id (int): User identifier
    - error (TonConnectError): Error information
    - rpc_request_id (int): Transaction request identifier
    - Additional parameters can be passed using `connector.add_event_kwargs(...)`
      Example: `connector.add_event_kwargs(event=Event.TRANSACTION, comment="Hello from tonutils!")`
      In this example, `comment` is an additional parameter that will be passed to the handler.

    The type of error can be determined using isinstance:
    - UserRejectsError: User declined the transaction.
    - RequestTimeoutError: Send request timed out for the transaction.
    """
    if isinstance(error, UserRejectsError):
        print(f"[Transaction ERROR] User rejected the transaction.")
    elif isinstance(error, RequestTimeoutError):
        print(f"[Transaction ERROR] Transaction request timed out.")
    else:
        print(f"[Transaction ERROR] Failed to send transaction: {error.message}")


async def main() -> None:
    user_id = 12345  # Example user identifier

    # Initialize the connector for the user
    connector = await tc.init_connector(user_id)

    # Start the event processing loop
    while True:
        # Check wallet connection
        if not connector.connected:
            print("Wallet not connected! Please connect the wallet to continue.")

            # Get all available wallets
            wallets = await tc.get_wallets()

            # As an example, we will select the wallet with index 1 (Tonkeeper)
            selected_wallet = wallets[1]
            connect_url = await connector.connect_wallet(selected_wallet)
            print(f"Please connect your wallet by visiting the following URL:\n{connect_url}")
            print("Waiting for wallet connection...")

            async with connector.connect_wallet_context() as response:
                if isinstance(response, TonConnectError):
                    print(f"Connection error: {response.message}")
                else:
                    print(f"Connected wallet: {response.account.address.to_str(is_bounceable=False)}")

        # If the wallet is connected, prompt the user to choose an action
        call = input(
            "\nChoose an action:\n"
            "1. Send a transaction\n"
            "2. Send a batch of transactions\n"
            "3. Disconnect wallet\n"
            "q. Quit\n"
            "\nEnter your choice: "
        ).strip()

        if call in ["1", "2"]:
            if call == "1":
                print("Preparing to send one transaction...")
                rpc_request_id = await connector.send_transfer(
                    destination=connector.account.address,
                    amount=0.000000001,
                    body="Hello from tonutils!",
                )
                print("Request to send one transaction has been sent.")
            else:
                print("Preparing to send a batch of transactions...")
                # Get the maximum number of messages supported in a transaction
                max_messages = connector.get_max_supported_messages()
                print(f"Maximum number of messages: {max_messages}. Sending {max_messages} transactions...")

                rpc_request_id = await connector.send_batch_transfer(
                    data_list=[
                        TransferData(
                            destination=connector.account.address,
                            amount=0.000000001,
                            body="Hello from tonutils!",
                        ) for _ in range(max_messages)  # Create the maximum number of messages
                    ]
                )
                print("Request to send a batch of transactions has been sent.")

            # Add additional parameters to be passed to event handlers
            connector.add_event_kwargs(event=Event.TRANSACTION, comment="Hello from tonutils!")

            # Get the transaction status (whether it has been confirmed by the user in the wallet)
            # Note: This is different from blockchain confirmation
            is_pending = connector.is_transaction_pending(rpc_request_id)
            print(f"Transaction is pending confirmation: {is_pending}")

            # In addition to the handler, you can use a context manager to get the transaction result by rpc_request_id
            async with connector.pending_transaction_context(rpc_request_id) as response:
                if isinstance(response, TonConnectError):
                    print(f"Error sending transaction: {response.message}")
                else:
                    print(f"Transaction successful! Hash: {response.normalized_hash}")

        elif call == "3":
            # Disconnect the wallet
            await connector.disconnect_wallet()
            print("Wallet successfully disconnected.")

        elif call.lower() == "q":
            print("Exiting the program...")
            break

        else:
            print("Invalid choice! Please select a valid option.")

    # Close all TonConnect connections
    await tc.close_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Ensure all connections are closed in case of interruption
        asyncio.run(tc.close_all())
```

Conclusion
----------

By following this cookbook, you can successfully integrate TonConnect into your script enabling seamless wallet
connections and transaction sending.
