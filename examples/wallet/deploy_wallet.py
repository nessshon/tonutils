from tonutils.client import TonapiClient
from tonutils.wallet import (
    WalletV3R1,
    # Uncomment the following lines to use different wallet versions:
    # WalletV3R2,
    # WalletV4R1,
    # WalletV4R2,
    # WalletV5R1,
    # HighloadWalletV2,
    # HighloadWalletV3,
    # PreprocessedWalletV2,
    # PreprocessedWalletV2R1,
)

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase for creating the wallet
MNEMONIC: list[str] = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV3R1.from_mnemonic(client, MNEMONIC)

    # Uncomment and use the following lines to create different wallet versions from mnemonic:
    # wallet, public_key, private_key, mnemonic = WalletV3R2.from_mnemonic(client, MNEMONIC)
    # wallet, public_key, private_key, mnemonic = WalletV4R1.from_mnemonic(client, MNEMONIC)
    # wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)
    # wallet, public_key, private_key, mnemonic = WalletV5R1.from_mnemonic(client, MNEMONIC)
    # wallet, public_key, private_key, mnemonic = HighloadWalletV2.from_mnemonic(client, MNEMONIC)
    # wallet, public_key, private_key, mnemonic = HighloadWalletV3.from_mnemonic(client, MNEMONIC)
    # wallet, public_key, private_key, mnemonic = PreprocessedWalletV2.from_mnemonic(client, MNEMONIC)
    # wallet, public_key, private_key, mnemonic = PreprocessedWalletV2R1.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.deploy()

    print(f"Wallet deployed successfully!")
    print(f"Wallet address: {wallet.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
