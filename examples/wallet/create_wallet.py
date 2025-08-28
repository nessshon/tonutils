from tonutils.clients import ToncenterClient
from tonutils.contracts import (
    # Uncomment the following lines to use different wallet versions:
    # WalletV1R1,
    # WalletV1R2,
    # WalletV1R3,
    # WalletV2R1,
    # WalletV2R2,
    # WalletV3R1,
    # WalletV3R2,
    # WalletV4R1,
    WalletV4R2,
    # WalletV5Beta,
    # WalletV5R1,
    # WalletHighloadV2,
    # WalletHighloadV3R1,
    # WalletPreprocessedV2,
)

# Set to True for testnet, False for mainnet
IS_TESTNET = True


def main() -> None:
    client = ToncenterClient(is_testnet=IS_TESTNET, rps=1)
    wallet, public_key, private_key, mnemonic = WalletV4R2.create(client)
    address = wallet.address.to_str(is_bounceable=False, is_test_only=IS_TESTNET)

    print(f"Address: {address}")
    print(f"Mnemonic: {' '.join(mnemonic)}")
    print(f"Keypair: {private_key.keypair.base64}")
    print(f"Private Key: {private_key.base64}")
    print(f"Public Key: {public_key.int}")


if __name__ == "__main__":
    main()
