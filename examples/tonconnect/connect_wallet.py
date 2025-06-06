from storage import FileStorage

from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import *
from tonutils.tonconnect.utils import generate_proof_payload
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


@tc.on_event(Event.CONNECT)
async def on_wallet_connect(user_id: int, wallet: WalletInfo) -> None:
    """
    Handle successful wallet connection.

    :param user_id: Identifier of the connected user.
    :param wallet: Connected wallet information.

    WalletInfo contains:
        - wallet.account: Address, chain ID, state init, and optional public key.
        - wallet.ton_proof: Domain, payload, signature, and timestamp.
        - wallet.device: Device information such as platform and app version.

    Additional parameters can be passed via `connector.add_event_kwargs()`.
    Example:
        connector.add_event_kwargs(event=Event.CONNECT, comment="example")
    """
    wallet_address = wallet.account.address.to_str(is_bounceable=False)
    print(f"[Event CONNECT] Wallet {wallet_address} connected to user {user_id}.")


@tc.on_event(EventError.CONNECT)
async def on_wallet_connect_error(user_id: int, error: TonConnectError) -> None:
    """
    Handle errors during wallet connection.

    :param user_id: Identifier of the user attempting connection.
    :param error: Raised error during the connection attempt.

    Recognized error types:
        - UserRejectsError: The user rejected the connection.
        - RequestTimeoutError: Wallet did not respond within timeout.

    Additional parameters can be passed via `connector.add_event_kwargs()`.
    """
    if isinstance(error, UserRejectsError):
        print(f"[EventError CONNECT] User {user_id} rejected the wallet connection.")
    elif isinstance(error, RequestTimeoutError):
        print(f"[EventError CONNECT] Connection request timed out for user {user_id}.")
    else:
        print(f"[EventError CONNECT] Connection error for user {user_id}: {error.message}")


@tc.on_event(Event.DISCONNECT)
async def on_wallet_disconnect(user_id: int, wallet: WalletInfo) -> None:
    """
    Handle successful wallet disconnection.

    :param user_id: Identifier of the user whose wallet was disconnected.
    :param wallet: Disconnected wallet information.

    Additional parameters can be passed via `connector.add_event_kwargs()`.
    Example:
        connector.add_event_kwargs(event=Event.DISCONNECT, comment="example")
    """
    wallet_address = wallet.account.address.to_str(is_bounceable=False)
    print(f"[Event DISCONNECT] Wallet {wallet_address} disconnected from user {user_id}.")


@tc.on_event(EventError.DISCONNECT)
async def on_wallet_disconnect_error(user_id: int, error: TonConnectError) -> None:
    """
    Handle errors during wallet disconnection.

    :param user_id: Identifier of the user whose wallet failed to disconnect.
    :param error: Raised error during the disconnect attempt.

    Recognized error types:
        - RequestTimeoutError: Wallet did not respond to the disconnect request.

    Additional parameters can be passed via `connector.add_event_kwargs()`.
    """
    if isinstance(error, RequestTimeoutError):
        print(f"[EventError DISCONNECT] Disconnect request timed out for user {user_id}.")
    else:
        print(f"[EventError DISCONNECT] Disconnect error for user {user_id}: {error.message}")


async def main() -> None:
    user_id = 12345  # Example user identifier

    # Initialize the connector for the user
    connector = await tc.init_connector(user_id)

    # Generate a TON Connect proof payload for authentication
    ton_proof = generate_proof_payload()

    # Check wallet connection
    if not connector.connected:
        print("Wallet not connected! Please connect the wallet to continue.")

        # Get all available wallets
        wallets = await tc.get_wallets()

        # As an example, we will select the wallet with index 1 (Tonkeeper)
        selected_wallet = wallets[1]
        connect_url = await connector.connect_wallet(selected_wallet, ton_proof=ton_proof)

        print(f"Please connect your wallet by visiting the following URL:\n{connect_url}")
        print("Waiting for wallet connection...")

        # Add additional parameters to be passed to event handlers
        connector.add_event_kwargs(event=Event.TRANSACTION, comment="Hello from tonutils!")

        # In addition to the handler, you can use a context manager to get the connection result
        async with connector.connect_wallet_context() as response:
            if isinstance(response, TonConnectError):
                print(f"Connection error: {response.message}")
            else:
                if connector.wallet.verify_proof_payload(ton_proof):
                    wallet_address = response.account.address.to_str(is_bounceable=False)
                    print(f"Connected wallet: {wallet_address}")
                else:
                    await connector.disconnect_wallet()
                    print("Proof verification failed.")
    else:
        wallet_address = connector.account.address.to_str(is_bounceable=False)
        print(f"Wallet already connected: {wallet_address}")

        user_input = input("Do you want to disconnect the wallet? (y/n): ").strip().lower()
        if user_input == "y":
            await connector.disconnect_wallet()
            print("Wallet successfully disconnected.")
        else:
            print("Wallet remains connected.")

    await tc.close_all()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        asyncio.run(tc.close_all())
