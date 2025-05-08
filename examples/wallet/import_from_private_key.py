from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2

# Private key (32 or 64 bytes)
PRIVATE_KEY: bytes = b"your_private_key_bytes"


def main() -> None:
    client = ToncenterV3Client()
    wallet = WalletV4R2.from_private_key(client, PRIVATE_KEY)

    print(f"Wallet address: {wallet.address.to_str()}")


if __name__ == "__main__":
    main()
