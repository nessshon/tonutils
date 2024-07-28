from tonutils.wallet import (
    WalletV3R1,
    WalletV3R2,
    WalletV4R1,
    WalletV4R2,
    HighloadWalletV2,
)


def main() -> None:
    # Create a WalletV3R1
    wallet, public_key, private_key, mnemonic = WalletV3R1.create()

    # or create a WalletV3R2
    # wallet, public_key, private_key, mnemonic = WalletV3R2.create()

    # or create a WalletV4R1
    # wallet, public_key, private_key, mnemonic = WalletV4R1.create()

    # or create a WalletV4R2
    # wallet, public_key, private_key, mnemonic = WalletV4R2.create()

    # or create a HighloadWalletV2
    # wallet, public_key, private_key, mnemonic = HighloadWalletV2.create()

    print("Wallet created!")
    print(f"Address: {wallet.address.to_str()}\nMnemonic: {mnemonic}\n")


if __name__ == "__main__":
    main()
