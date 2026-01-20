from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV4Config, WalletV4R2
from tonutils.types import NetworkGlobalID, PrivateKey

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Private key can be provided in multiple formats:
# - bytes: raw binary representation
# - hex string: hexadecimal encoding
# - base64 string: base64 encoding
# - integer: numeric representation
PRIVATE_KEY = PrivateKey("<your private key>")


def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)

    # Wallet configuration (default settings)
    # Can customize subwallet_id for multiple wallets from same mnemonic
    config = WalletV4Config()

    # Option 1: Create wallet from mnemonic phrase
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC, config=config)

    # Option 2: Create wallet from existing private key
    # Use when you already have the private key
    wallet = WalletV4R2.from_private_key(client, PRIVATE_KEY, config=config)

    # Get wallet address in user-friendly format
    # is_bounceable=False: standard for wallet contracts (UQ...)
    print(f"Wallet address: {wallet.address.to_str(is_bounceable=False)}")


if __name__ == "__main__":
    main()
