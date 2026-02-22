from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.storage import FileStorage
from tonutils.tonconnect.utils import AppWalletsLoader
from tonutils.types import NetworkGlobalID

# URL to your tonconnect-manifest.json (must be publicly accessible)
# The wallet fetches this to display your app's name and icon
MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/v2.0/assets/tonconnect-manifest.json"

# Unique session key — identifies this connection in storage
# In production use a per-user identifier (e.g. Telegram user_id)
SESSION_KEY = "user-123"

# Path to the JSON file used as key-value storage for session data
# FileStorage is suitable for single-process apps; replace with a custom
# StorageProtocol implementation for distributed or database-backed setups
STORAGE_PATH = "./tonconnect-storage.json"


async def main() -> None:
    storage = FileStorage(STORAGE_PATH)

    # Load wallet descriptors from the TON wallets registry
    # include_wallets: restrict to specific wallets — reduces bridge connections opened
    app_wallets_loader = AppWalletsLoader(include_wallets=["tonkeeper"])

    # Initialize the TonConnect manager
    # manifest_url: publicly accessible URL to your tonconnect-manifest.json
    # storage:      persistent session backend (FileStorage, Redis, DB, etc.)
    # app_wallets:  wallet descriptors propagated to each connector as bridge connection sources
    tc = TonConnect(
        storage=storage,
        manifest_url=MANIFEST_URL,
        app_wallets=app_wallets_loader.get_wallets(),
    )

    # Create a connector for this session
    # Each user/session gets its own connector with an isolated storage namespace
    connector = tc.create_connector(SESSION_KEY)

    # Try to restore a previously saved connection before starting a new one
    # Returns True if an active session was found in storage
    restored = await connector.restore()

    if restored:
        print(f"Session restored")
        print(f"Address: {connector.account.address.to_str(is_bounceable=False)}")
    else:
        # Build a connect request with only the address item (no TonProof)
        # Use make_connect_request(ton_proof_payload=...) to also request ownership proof
        request = connector.make_connect_request()

        # Initiate connection and get the standard tc:// universal link
        # network:  expected network — rejects wallets connected to a different chain
        # timeout:  seconds before the pending connect is canceled (default: 15 min)
        standard_url = await connector.connect(
            request=request,
            network=NetworkGlobalID.TESTNET,
        )

        # Standard tc:// link — works with any TonConnect-compatible wallet
        print(f"Connect URL: {standard_url}")

        # Wallet-specific universal link — opens directly in the target wallet app
        # Uses app_wallet.universal_url as the base instead of tc://
        # Bridge connection sources are not affected by this parameter
        tonkeeper = app_wallets_loader.get_wallet("tonkeeper")
        tonkeeper_url = connector.make_connect_url(request, tonkeeper)
        print(f"Tonkeeper URL: {tonkeeper_url}")

        # Block until the wallet responds (approve or reject)
        # Returns (wallet, None) on success, (None, error) on failure or timeout
        wallet, error = await connector.wait_connect()

        if error:
            print(f"Connection failed: {error}")
            return

        print(f"Connected to: {connector.app_wallet.name}")
        print(f"Address: {connector.account.address.to_str(is_bounceable=False)}")
        print(f"Network: {connector.account.network.name}")

    # Close all active bridge connections
    await tc.close_all()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
