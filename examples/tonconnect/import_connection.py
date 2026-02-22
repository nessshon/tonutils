from pytoniq_core import Address

from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.models import (
    ActiveConnection,
    SendTransactionMessage,
    SendTransactionPayload,
)
from tonutils.tonconnect.storage import FileStorage
from tonutils.tonconnect.utils import AppWalletsLoader
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

# Raw bridge connection data exported from TonConnect UI storage
# Corresponds to the value stored under key: ton-connect-storage_bridge-connection
# Contains the connect event payload, session key pair, and bridge URL
BRIDGE_CONNECTION = {
    "type": "http",
    "connectEvent": {
        "id": 1771782910,
        "event": "connect",
        "payload": {
            "items": [
                {
                    "walletStateInit": "te6cckECFgEAAwQAAgE0AgEAUQAAAAApqaMXkasCAZJ5CdXbkW0LauiW8vn2icHXdH/BadZ7NvZCgS9AART/APSkE/S88sgLAwIBIAkEBPjygwjXGCDTH9Mf0x8C+CO78mTtRNDTH9Mf0//0BNFRQ7ryoVFRuvKiBfkBVBBk+RDyo/gAJKTIyx9SQMsfUjDL/1IQ9ADJ7VT4DwHTByHAAJ9sUZMg10qW0wfUAvsA6DDgIcAB4wAhwALjAAHAA5Ew4w0DpMjLHxLLH8v/CAcGBQAK9ADJ7VQAbIEBCNcY+gDTPzBSJIEBCPRZ8qeCEGRzdHJwdIAYyMsFywJQBc8WUAP6AhPLassfEss/yXP7AABwgQEI1xj6ANM/yFQgR4EBCPRR8qeCEG5vdGVwdIAYyMsFywJQBs8WUAT6AhTLahLLH8s/yXP7AAIAbtIH+gDU1CL5AAXIygcVy//J0Hd0gBjIywXLAiLPFlAF+gIUy2sSzMzJc/sAyEAUgQEI9FHypwICAUgSCgIBIAwLAFm9JCtvaiaECAoGuQ+gIYRw1AgIR6STfSmRDOaQPp/5g3gSgBt4EBSJhxWfMYQCASAODQARuMl+1E0NcLH4AgFYEQ8CASAVEAAZrx32omhAEGuQ64WPwAA9sp37UTQgQFA1yH0BDACyMoHy//J0AGBAQj0Cm+hMYALm0AHQ0wMhcbCSXwTgItdJwSCSXwTgAtMfIYIQcGx1Z70ighBkc3RyvbCSXwXgA/pAMCD6RAHIygfL/8nQ7UTQgQFA1yH0BDBcgQEI9ApvoTGzkl8H4AXTP8glghBwbHVnupI4MOMNA4IQZHN0crqSXwbjDRQTAIpQBIEBCPRZMO1E0IEBQNcgyAHPFvQAye1UAXKwjiOCEGRzdHKDHrFwgBhQBcsFUAPPFiP6AhPLassfyz/JgED7AJJfA+IAeAH6APQEMPgnbyIwUAqhIb7y4FCCEHBsdWeDHrFwgBhQBMsFJs8WWPoCGfQAy2kXyx9SYMs/IMmAQPsABgAZrc52omhAIGuQ64X/wDa5rXc=",
                    "network": "-3",
                    "address": "0:bede2955afe5b451cde92eb189125c12685c6f8575df922400dc4c1d5411cd35",
                    "name": "ton_addr",
                    "publicKey": "91ab0201927909d5db916d0b6ae896f2f9f689c1d7747fc169d67b36f642812f",
                }
            ],
            "device": {
                "features": [
                    "SendTransaction",
                    {"maxMessages": 4, "name": "SendTransaction"},
                    {"types": ["text", "binary", "cell"], "name": "SignData"},
                ],
                "appName": "Tonkeeper",
                "appVersion": "5.4.2",
                "maxProtocolVersion": 2,
                "platform": "iphone",
            },
        },
    },
    "session": {
        "sessionKeyPair": {
            "publicKey": "6f096af7d1d0301ad5a52c755a00d981811d45493cf518d1cef80ca871a8f376",
            "secretKey": "5dc47422a836cccabe4326fe0adfc25cb0ab6ce0af4f9fa6f738967da4354e7d",
        },
        "walletPublicKey": "bb73ded6f4a0f3672fdc2ddc5da3c4dbd81ade23bb64a317b8ddf825d962be3a",
        "bridgeUrl": "https://bridge.tonapi.io/bridge",
    },
    "lastWalletEventId": 1771782910,
    "nextRpcRequestId": 0,
}

# Last event ID exported from TonConnect UI storage
# Corresponds to the value stored under key: ton-connect-storage_http-bridge-gateway
# Used to resume the SSE stream from where it left off and avoid replaying old events
BRIDGE_LAST_EVENT_ID = "1770180433054700"


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

    # Merge bridge connection data with the last event ID into a single dict
    # lastEventId is kept separate in TonConnect UI storage but required by ActiveConnection
    connection = {**BRIDGE_CONNECTION, "lastEventId": BRIDGE_LAST_EVENT_ID}

    # Parse and validate the merged dict into a typed ActiveConnection model
    active_connection = ActiveConnection.model_validate(connection)

    # Reconstruct a connector from the existing connection — no new connect flow needed
    # Stores the connection in provider storage and restores the wallet session
    connector = await tc.from_connection(active_connection, SESSION_KEY)

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
