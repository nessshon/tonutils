from storage import FileStorage
from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import Event, EventError, WalletInfo
from tonutils.tonconnect.utils.exceptions import TonConnectError, UserRejectsError, RequestTimeoutError

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
