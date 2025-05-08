from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."


def main() -> None:
    client = ToncenterV3Client()
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)

    print(f"Wallet address: {wallet.address.to_str()}")


if __name__ == "__main__":
    main()
