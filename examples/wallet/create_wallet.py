from tonutils.client import TonapiClient
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

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True


def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.create(client)

    # Uncomment and use the following lines to create different wallet versions:
    # wallet, public_key, private_key, mnemonic = WalletV3R2.create(client)
    # wallet, public_key, private_key, mnemonic = WalletV4R1.create(client)
    # wallet, public_key, private_key, mnemonic = WalletV4R2.create(client)
    # wallet, public_key, private_key, mnemonic = WalletV5R1.create(client)
    # wallet, public_key, private_key, mnemonic = HighloadWalletV2.create(client)
    # wallet, public_key, private_key, mnemonic = HighloadWalletV3.create(client)
    # wallet, public_key, private_key, mnemonic = PreprocessedWalletV2.create(client)
    # wallet, public_key, private_key, mnemonic = PreprocessedWalletV2R1.create(client)

    print("Wallet has been successfully created!")
    print(f"Address: {wallet.address.to_str()}")
    # Print user friendly address https://docs.ton.org/v3/guidelines/dapps/cookbook
    print(f"Testnet address: {wallet.address.to_str(is_test_only=IS_TESTNET)}")
    # Expected testnet bounceable address example: kQCbWHf3WxKD5FtPXYnFAZcPT3aAC8TqdXhHPxNXcHYW_a0Y
    # Note: For you first transaction you need to use non-bounceable address
    print(f"Mnemonic: {mnemonic}")


if __name__ == "__main__":
    main()
