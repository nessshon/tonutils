# Transaction Sending Cookbook

Welcome to the **Transaction Sending Cookbook**! This guide provides step-by-step instructions for integrating and
managing transaction sending using the `TonConnect` from the `tonutils` library. Whether you're a beginner or an
experienced developer, this cookbook will help you implement transaction functionality efficiently.

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

Handling events is essential for responding to transaction actions and errors. There are two primary methods to handle
events: using decorators and using context managers.

#### Using Decorators

Decorators associate event handlers with specific events. This method is straightforward and keeps your event handling
logic organized.

```python
@tc.on_event(Event.TRANSACTION)
async def on_transaction(transaction: SendTransactionResponse) -> None:
    print(f"[Transaction SENT] Transaction successfully sent. Message hash: {transaction.hash}")
```

#### Using Context Managers

Context managers provide a controlled environment for handling events, ensuring proper setup and teardown.

```python
async with connector.pending_transaction_context(rpc_request_id) as response:
    if isinstance(response, TonConnectError):
        print(f"Error sending transaction: {response.message}")
    else:
        print(f"Transaction successful! Hash: {response.hash}")
```

#### Passing Additional Parameters to Event Handlers

You can pass additional parameters to event handlers using `connector.add_event_kwargs`. This allows handlers to receive
extra information beyond the default parameters.

##### Example:

```python
connector.add_event_kwargs(event=Event.TRANSACTION, comment="Hello from tonutils!")
```

```python
@tc.on_event(Event.TRANSACTION)
async def on_transaction(user_id: int, transaction: SendTransactionResponse, comment: str) -> None:
    print(comment)
```

### Sending Transactions

#### Sending a Single Transaction

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

#### Sending a Batch of Transactions

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

#### Handling Transaction Status

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
        print(f"Transaction successful! Hash: {response.hash}")
````

### Example Usage

Below is a comprehensive example demonstrating connector initialization, event handling, sending transactions, and
wallet management.

```python
import asyncio
import logging

from storage import FileStorage

from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import Event, EventError, SendTransactionResponse
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError, RequestTimeoutError
from tonutils.wallet.data import TransferData

# URL of the publicly hosted JSON manifest of the application
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"  # noqa

# Initialize storage to save connected wallet data
TC_STORAGE = FileStorage("connection.json")

# Create an instance of TonConnect with storage and manifest
tc = TonConnect(storage=TC_STORAGE, manifest_url=TC_MANIFEST_URL)


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
    - transaction.hash (str): Message hash (different from the actual transaction hash)
    - transaction.cell (Cell): Transaction Cell
    """
    print(f"[Transaction SENT] Transaction successfully sent. Message hash: {transaction.hash}")


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
            break

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
                    print(f"Transaction successful! Hash: {response.hash}")

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

## Conclusion

By following this cookbook, you can successfully integrate TonConnect into your script enabling seamless wallet
connections and transaction sending.
