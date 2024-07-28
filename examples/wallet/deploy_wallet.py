from tonutils.client import TonapiClient
from tonutils.wallet import (
    WalletV3R1,
    WalletV3R2,
    WalletV4R1,
    WalletV4R2,
    HighloadWalletV2,
)

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)

    # Create a WalletV3R1 from mnemonic
    wallet, public_key, private_key, mnemonic = WalletV3R1.from_mnemonic(MNEMONIC, client)

    # or create a WalletV3R2 from mnemonic
    # wallet, public_key, private_key, mnemonic = WalletV3R2.from_mnemonic(MNEMONIC, client)

    # or create a WalletV4R1 from mnemonic
    # wallet, public_key, private_key, mnemonic = WalletV4R1.from_mnemonic(MNEMONIC, client)

    # or create a WalletV4R2 from mnemonic
    # wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(MNEMONIC, client)

    # or create a HighloadWalletV2 from mnemonic
    # wallet, public_key, private_key, mnemonic = HighloadWalletV2.from_mnemonic(MNEMONIC, client)

    tx_hash = await wallet.deploy()

    print(f"Deployed wallet address: {wallet.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
