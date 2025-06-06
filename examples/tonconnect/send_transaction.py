from storage import FileStorage

from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import *
from tonutils.tonconnect.utils.exceptions import *
from tonutils.wallet.messages import TransferMessage

# Public URL to the application manifest.
# The manifest defines app metadata (name, icon, URL, permissions).
# Reference: https://github.com/ton-blockchain/ton-connect/blob/main/requests-responses.md#app-manifest
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"

# Storage backend for persisting wallet connection data.
# File-based implementation using aiofiles.
TC_STORAGE = FileStorage("connection.json")

# Initialize TonConnect with storage, manifest, and fallback wallet list.
tc = TonConnect(
    storage=TC_STORAGE,
    manifest_url=TC_MANIFEST_URL,
    wallets_fallback_file_path="./wallets.json"
)


@tc.on_event(Event.TRANSACTION)
async def on_transaction(transaction: SendTransactionResponse) -> None:
    """
    Handle successful transaction event.

    :param transaction: Transaction response containing BoC, hash, and message cell.

    Transaction details:
        - transaction.boc (str): Raw BoC of the outgoing message.
        - transaction.normalized_hash (str): Hash of the message for tracking.
        - transaction.cell (Cell): Parsed message cell.

    Additional parameters can be passed via `connector.add_event_kwargs()`.
    Example:
        connector.add_event_kwargs(event=Event.TRANSACTION, comment="example")
    """
    print(f"[Event TRANSACTION] Transaction sent successfully. Message hash: {transaction.normalized_hash}")


@tc.on_event(EventError.TRANSACTION)
async def on_transaction_error(error: TonConnectError) -> None:
    """
    Handle errors during transaction sending.

    :param error: Error raised when the transaction could not be processed.

    Recognized error types:
        - UserRejectsError: The user rejected the transaction.
        - RequestTimeoutError: The wallet did not respond in time.

    Additional parameters can be passed via `connector.add_event_kwargs()`.
    """
    if isinstance(error, UserRejectsError):
        print("[EventError TRANSACTION] User rejected the transaction.")
    elif isinstance(error, RequestTimeoutError):
        print("[EventError TRANSACTION] Transaction request timed out.")
    else:
        print(f"[EventError TRANSACTION] Failed to send transaction: {error.message}")


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
                    continue
                wallet_address = response.account.address.to_str(is_bounceable=False)
                print(f"Connected wallet: {wallet_address}")

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
                max_messages = connector.device.get_max_supported_messages(connector.wallet)
                print(f"Maximum number of messages: {max_messages}. Sending {max_messages} transactions...")

                rpc_request_id = await connector.send_batch_transfer(
                    messages=[
                        TransferMessage(
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
            is_pending = connector.is_request_pending(rpc_request_id)
            print(f"Transaction is pending confirmation: {is_pending}")

            # In addition to the handler, you can use a context manager to get the transaction result by rpc_request_id
            async with connector.pending_request_context(rpc_request_id) as response:
                if isinstance(response, TonConnectError):
                    print(f"Error sending transaction: {response.message}")
                else:
                    print(f"Transaction successful! Hash: {response.normalized_hash}")

        elif call == "3":
            await connector.disconnect_wallet()
            print("Wallet successfully disconnected.")
            continue

        elif call.lower() == "q":
            print("Exiting the program...")
            break

        else:
            print("Invalid choice! Please select a valid option.")

    await tc.close_all()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        asyncio.run(tc.close_all())
