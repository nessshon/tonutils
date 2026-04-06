from ton_core import NetworkGlobalID, to_nano

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV4R2

# Mnemonic phrase — 24 words (TON-native) or 12/18/24 words (BIP-39 import)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Deploy wallet by sending any transaction
    # Sending 0.05 TON to self deploys the wallet contract
    # Wallet auto-deploys on first outgoing transaction if in uninit status
    # After deployment, wallet transitions from uninit to active status
    msg = await wallet.transfer(destination=wallet.address, amount=to_nano(0.05))

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
