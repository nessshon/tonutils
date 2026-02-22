from nacl.exceptions import BadSignatureError

from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import (
    SignDataPayloadDto,
    SignDataPayloadText,
)
from tonutils.tonconnect.storage import FileStorage
from tonutils.tonconnect.utils import AppWalletsLoader
from tonutils.tonconnect.utils.signing import VerifySignData
from tonutils.types import NetworkGlobalID

# URL to your tonconnect-manifest.json (must be publicly accessible)
# The wallet fetches this to display your app's name and icon
MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/v2.0/assets/tonconnect-manifest.json"

# Unique session key — identifies this connection in storage
# In production use a per-user identifier (e.g. Telegram user_id)
SESSION_KEY = "user-123"

# Domain your app is served from — included in the signed message
# Must match the domain in your tonconnect-manifest.json
APP_DOMAIN = "github.com"

# Path to the JSON file used as key-value storage for session data
# FileStorage is suitable for single-process apps; replace with a custom
# StorageProtocol implementation for distributed or database-backed setups
STORAGE_PATH = "./tonconnect-storage.json"

# Text the user will be asked to sign in their wallet UI
SIGN_TEXT = "I agree to the Terms of Service"


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

    # Build the sign data payload
    # Supported payload types: SignDataPayloadText, SignDataPayloadBinary, SignDataPayloadCell
    # text: UTF-8 string shown to the user in the wallet UI
    payload = SignDataPayloadText(text=SIGN_TEXT)

    # Send the sign data request to the connected wallet
    # Returns a request_id immediately — the user approves in their wallet app
    # Automatically verifies SignData feature support before sending
    request_id = await connector.sign_data(payload)
    print(f"Sign request sent, waiting for confirmation...")

    # Block until the wallet signs the data (or rejects/times out)
    # Returns (result, None) on success, (None, error) on rejection or timeout
    result, error = await connector.wait_sign_data(request_id)

    if error:
        print(f"Signing failed: {error}")
        return

    # Signature hex and unix timestamp when the wallet produced it
    print(f"Signature: {result.signature.as_hex}")
    print(f"Signed at: {result.timestamp}")

    try:
        # Verify the signature returned by the wallet
        # Reconstructs the canonical signing message from the result and verifies:
        #   1. Public key extracted from walletStateInit matches publicKey field
        #   2. Address derived from walletStateInit matches address field
        #   3. Timestamp is within valid_auth_time window (prevents replay attacks)
        #   4. Domain is in allowed_domains (prevents cross-app reuse)
        #   5. Ed25519 signature over the canonical message is valid
        sign_data_payload = SignDataPayloadDto(
            address=connector.account.address,
            network=connector.account.network,
            public_key=connector.account.public_key,
            wallet_state_init=connector.account.state_init,
            signature=result.signature,
            timestamp=result.timestamp,
            domain=result.domain,
            payload=result.payload,
        )
        await VerifySignData(sign_data_payload).verify(
            allowed_domains=[APP_DOMAIN],
            valid_auth_time=5 * 60,  # 5 minutes
        )
        print(f"SignData verified")
    except BadSignatureError as e:
        print(f"SignData verification failed: {e}")

    # Close all active bridge connections
    await tc.close_all()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
