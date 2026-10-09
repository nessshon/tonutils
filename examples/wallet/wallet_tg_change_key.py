from ton_core import NetworkGlobalID

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletTg

# Mnemonic phrase — TON or Multichain (BIP-39)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# New mnemonic to rotate the signing key to
NEW_MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # If the key was already rotated, the address no longer derives from the
    # mnemonic — open it with from_address_and_mnemonic (see wallet_tg_open_by_address.py)
    wallet, _, _, _ = WalletTg.from_mnemonic(client, MNEMONIC)

    # Rotate the signing key to NEW_MNEMONIC
    # The request is signed twice: by the current key (authorizes the change)
    # and by the new key (proves ownership of the key being installed)
    # The wallet address does not change — only the on-chain public key does,
    # so the balance and history stay on the same address
    # After acceptance, reopen the wallet with NEW_MNEMONIC via from_address_and_mnemonic
    # Returns: (external_message, public_key, private_key, mnemonic)
    msg, _, _, _ = await wallet.change_public_key_from_mnemonic(NEW_MNEMONIC)

    # Get wallet address in user-friendly format
    # is_bounceable=False: standard for wallet contracts (UQ...)
    print(f"Wallet address: {wallet.address.to_str(is_bounceable=False)}")

    # Normalized hash of the signed external message (computed locally before sending)
    # Not a blockchain transaction hash — use it to track whether the message
    # was accepted on-chain (e.g. via explorers, API queries, or your own checks)
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
