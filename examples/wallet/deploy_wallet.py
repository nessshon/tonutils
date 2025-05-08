from tonutils.client import ToncenterV3Client
from tonutils.wallet import (
    # Uncomment the following lines to use different wallet versions:
    # WalletV2R1,
    # WalletV2R2,
    # WalletV3R1,
    # WalletV3R2,
    # WalletV4R1,
    WalletV4R2,
    # WalletV5R1,
    # HighloadWalletV2,
    # HighloadWalletV3,
    # PreprocessedWalletV2,
    # PreprocessedWalletV2R1,
)

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Uncomment and use the following lines to create different wallet versions from mnemonic:
    # wallet, public_key, private_key, mnemonic = WalletV2R1.from_mnemonic(client, MNEMONIC)
    # wallet, public_key, private_key, mnemonic = WalletV2R2.from_mnemonic(client, MNEMONIC)
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
