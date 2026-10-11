from ton_core import NetworkGlobalID, multichain_mnemonic_new

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletTg

# Telegram wallet mnemonic — 12 words, or 24 after a key rotation
# Words 1-12 derive the address, words 13-24 hold the current signing key
MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletTg.from_mnemonic(client, MNEMONIC)

    # New mnemonic: words 1-12 of the current one and a new 12-word half
    # Store it before rotating: it is the only copy of the new key
    new_mnemonic = MNEMONIC.split()[:12] + multichain_mnemonic_new()
    print(f"New mnemonic: {' '.join(new_mnemonic)}")

    # Rotate the signing key to words 13-24 of the new mnemonic
    # The wallet address does not change — only the on-chain public key does,
    # so the balance and history stay on the same address
    # After acceptance, open the wallet with from_mnemonic(client, new_mnemonic)
    msg = await wallet.rotate_mnemonic(new_mnemonic)

    # Normalized hash of the signed external message (computed locally before sending)
    # Not a blockchain transaction hash — use it to track whether the message
    # was accepted on-chain (e.g. via explorers, API queries, or your own checks)
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
