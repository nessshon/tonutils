from pytoniq_core import begin_cell
from storage import FileStorage

from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import *
from tonutils.tonconnect.utils.exceptions import *

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


@tc.on_event(Event.SIGN_DATA)
async def on_sign_data(sign_data: SignDataResponse) -> None:
    """
    Handle successful sign data event.

    :param sign_data: Response containing signed data result.

    SignDataResponse details:
        - sign_data.result (str): Base64-encoded signed payload.
        - sign_data.original (dict): Original payload that was signed.

    Additional parameters can be passed via `connector.add_event_kwargs()`.
    Example:
        connector.add_event_kwargs(event=Event.SIGN_DATA, comment="example")
    """
    print(f"[Event SIGN_DATA] Data to sign: {sign_data.result}")


@tc.on_event(EventError.SIGN_DATA)
async def on_sign_data_error(error: TonConnectError) -> None:
    """
    Handle errors during sign data request.

    :param error: Error raised when sign data could not be processed.

    Recognized error types:
        - UserRejectsError: The user rejected the sign data request.
        - RequestTimeoutError: The wallet did not respond in time.

    Additional parameters can be passed via `connector.add_event_kwargs()`.
    """
    if isinstance(error, UserRejectsError):
        print("[EventError SIGN_DATA] User rejected the sign data request.")
    elif isinstance(error, RequestTimeoutError):
        print("[EventError SIGN_DATA] Sign data request timed out.")
    else:
        print(f"[EventError SIGN_DATA] Failed to send sign data: {error.message}")


async def main() -> None:
    user_id = 12345  # Example user identifier

    # Initialize the connector for the user
    connector = await tc.init_connector(user_id)

    # Start the event processing loop
    while True:
        # Check wallet connection
        if not connector.connected:
            print("Wallet not connected. Please connect a wallet to continue.")

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

        call = input(
            "\nChoose an action:\n"
            "1. Sign Text Data\n"
            "2. Sign Binary Data\n"
            "3. Sign Cell Data\n"
            "d. Disconnect Wallet\n"
            "q. Quit\n"
            "\nEnter your choice: "
        ).strip().lower()

        if call == "q":
            print("Exiting the program...")
            break

        elif call == "d":
            await connector.disconnect_wallet()
            print("Wallet successfully disconnected.")
            continue

        elif call in {"1", "2", "3"}:
            data = "Hello from tonutils!"

            if call == "1":
                payload = SignDataPayloadText(text=data)
            elif call == "2":
                payload = SignDataPayloadBinary(bytes=data.encode("utf-8"))
            else:
                payload = SignDataPayloadCell(
                    cell=begin_cell().store_uint(0, 32).store_snake_string(data).end_cell(),
                    schema="text_comment#00000000 text:Snakedata = InMsgBody;"
                )

            try:
                connector.device.verify_sign_data_feature(connector.wallet, payload)
            except WalletNotSupportFeatureError:
                print("Wallet does not support sign data feature.")
                continue

            rpc_request_id = await connector.sign_data(payload)

            # Add additional parameters to be passed to event handlers
            connector.add_event_kwargs(event=Event.SIGN_DATA, comment="Hello from tonutils!")

            # Get the transaction status (whether it has been confirmed by the user in the wallet)
            # Note: This is different from blockchain confirmation
            is_pending = connector.is_request_pending(rpc_request_id)
            print(f"Sign data is pending confirmation: {is_pending}")

            # In addition to the handler, you can use a context manager to get the sign data result by rpc_request_id
            async with connector.pending_request_context(rpc_request_id) as response:
                if isinstance(response, TonConnectError):
                    print(f"Error sending sign data: {response.message}")
                else:
                    key = connector.wallet.account.public_key
                    if response.verify_sign_data(key):
                        print("Verified sign data.")
                    else:
                        print("Failed to verify sign data.")
        else:
            print("Invalid choice. Please select a valid option.")

    await tc.close_all()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        asyncio.run(tc.close_all())
