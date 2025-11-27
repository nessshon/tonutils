from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import WalletV4Config, WalletV4R2
from tonutils.types import NetworkGlobalID, PrivateKey

MNEMONIC = "word1 word2 word3 ..."

# Can be: bytes, hex string, base64 string or integer
PRIVATE_KEY = PrivateKey("your_private_key")


def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)

    config = WalletV4Config()

    # Option 1: from mnemonic
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC, config=config)
    # Option 2: from private key
    wallet = WalletV4R2.from_private_key(client, PRIVATE_KEY, config=config)

    print(f"Wallet address: {wallet.address.to_str(is_bounceable=False)}")


if __name__ == "__main__":
    main()
