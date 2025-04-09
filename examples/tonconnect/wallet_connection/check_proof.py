from storage import FileStorage
from tonutils.tonconnect import TonConnect
from tonutils.tonconnect.utils.exceptions import TonConnectError
from tonutils.tonconnect.utils.proof import generate_proof_payload, verify_proof_payload

# URL of the publicly hosted JSON manifest of the application
# For detailed information: https://github.com/ton-blockchain/ton-connect/blob/main/requests-responses.md#app-manifest
TC_MANIFEST_URL = "https://raw.githubusercontent.com/nessshon/tonutils/main/examples/tonconnect/tonconnect-manifest.json"  # noqa

# Initialize storage to save connected wallet data
# In this example, FileStorage from storage.py is used
TC_STORAGE = FileStorage("connection.json")

# Create an instance of TonConnect with the specified storage and manifest
tc = TonConnect(storage=TC_STORAGE, manifest_url=TC_MANIFEST_URL, wallets_fallback_file_path="./wallets.json")


async def main() -> None:
    user_id = 1  # Example user ID

    # Initialize the connector for the user
    connector = await tc.init_connector(user_id)

    # Generate the proof payload
    proof_payload = generate_proof_payload()

    # Check if the wallet is already connected
    if not connector.connected:
        # Get all available wallets
        wallets = await tc.get_wallets()

        # As an example, we will select the wallet with index 1 (Tonkeeper)
        selected_wallet = wallets[1]
        connect_url = await connector.connect_wallet(selected_wallet, ton_proof=proof_payload)
        print(f"Please connect your wallet by visiting the following URL:\n{connect_url}")

        print("Waiting for wallet connection...")
        async with connector.connect_wallet_context() as response:
            if isinstance(response, TonConnectError):
                print(f"Connection error: {response.message}")
            else:
                if verify_proof_payload(proof_payload, connector.wallet):
                    print(f"Connected wallet: {response.account.address.to_str(is_bounceable=False)}")
                else:
                    await connector.disconnect_wallet()
                    print("Proof verification failed.")

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
