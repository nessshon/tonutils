from pytoniq_core import Address

from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import (
    SendTransactionMessage,
    SendTransactionPayload,
)
from tonutils.tonconnect.storage import FileStorage
from tonutils.tonconnect.utils import AppWalletsLoader
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

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

# Recipient address (regular wallet address, non-bounceable format)
DESTINATION_ADDRESS = Address("UQ...")

# Comment attached to the transfer (optional, visible in explorers)
TRANSFER_COMMENT = "Hello from tonutils!"

# Amount in nanotons (1 TON = 1,000,000,000 nanotons)
TRANSFER_AMOUNT = to_nano(0.01)


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

    if not restored:
        request = connector.make_connect_request()

        # Initiate connection and get the standard tc:// universal link
        # network:  expected network — rejects wallets connected to a different chain
        # timeout:  seconds before the pending connect is canceled (default: 15 min)
        await connector.connect(
            request=request,
            network=NetworkGlobalID.TESTNET,
        )

        # Wallet-specific universal link — opens directly in the target wallet app
        # Uses app_wallet.universal_url as the base instead of tc://
        tonkeeper = app_wallets_loader.get_wallet("tonkeeper")
        tonkeeper_url = connector.make_connect_url(request, tonkeeper)
        print(f"Tonkeeper URL: {tonkeeper_url}")

        # Block until the wallet responds (approve or reject)
        # Returns (wallet, None) on success, (None, error) on failure or timeout
        wallet, error = await connector.wait_connect()

        if error:
            print(f"Connection failed: {error}")
            return

    address = connector.account.address.to_str(is_bounceable=False)
    print(f"Address: {address}")

    # Build the transaction payload
    # messages:    list of outgoing messages (most wallets support up to 4)
    # valid_until: Unix timestamp after which the transaction is rejected by the wallet
    #              also used as the request timeout — wallet UI shows a countdown
    payload = SendTransactionPayload(
        messages=[
            # address: destination Address or raw string
            # amount:  in nanotons (1 TON = 1,000,000,000 nanotons)
            # payload: optional message body — Cell (jetton transfer, etc.) or string (text comment)
            SendTransactionMessage(
                address=DESTINATION_ADDRESS,
                amount=TRANSFER_AMOUNT,
                payload=TRANSFER_COMMENT,
            ),
        ],
    )

    # Send the transaction request to the connected wallet
    # Returns a request_id immediately — the user approves in their wallet app
    # Automatically verifies SendTransaction feature support before sending
    request_id = await connector.send_transaction(payload)
    print(f"Transaction sent, waiting for confirmation...")

    # Block until the wallet signs and submits the transaction (or rejects/times out)
    # Returns (result, None) on success, (None, error) on rejection or timeout
    result, error = await connector.wait_transaction(request_id)

    if error:
        print(f"Transaction failed: {error}")
    else:
        # boc: signed transaction BoC — use it to track the transaction on-chain
        print(f"Transaction boc : {result.boc}")
        print(f"Transaction hash: {result.normalized_hash}")

    # Close all active bridge connections
    await tc.close_all()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
