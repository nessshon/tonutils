from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV4R2

IS_TESTNET = True

MNEMONIC = "word1 word2 word3 ..."

# Private key (32 bytes or full keypair 64 bytes)
PRIVATE_KEY: bytes = b"your_private_key_bytes"


def main() -> None:
    client = ToncenterClient(is_testnet=IS_TESTNET)

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)
    # or
    # wallet = WalletV4R2.from_private_key(client, PrivateKey(PRIVATE_KEY))

    address = wallet.address.to_str(is_bounceable=False, is_test_only=IS_TESTNET)

    print(f"Wallet address: {address}")


if __name__ == "__main__":
    main()
