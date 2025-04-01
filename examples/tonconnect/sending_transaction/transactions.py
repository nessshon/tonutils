from storage import FileStorage
from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import Event, EventError, SendTransactionResponse
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError, RequestTimeoutError
from tonutils.wallet.data import TransferData

# URL of the publicly hosted JSON manifest of the application
# For detailed information: https://github.com/ton-blockchain/ton-connect/blob/main/requests-responses.md#app-manifest
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"  # noqa

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
            # After this, you can use:
            """
            @tc.on_event(Event.TRANSACTION)
            async def on_transaction(transaction: SendTransactionResponse, comment: str) -> None:...
            """

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
    import asyncio

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        # Ensure all connections are closed in case of interruption
        asyncio.run(tc.close_all())
