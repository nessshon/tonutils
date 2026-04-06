from ton_core import Address, NetworkGlobalID, to_nano

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV4R2

# Mnemonic phrase — 24 words (TON-native) or 12/18/24 words (BIP-39 import)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Destination address (recipient)
DESTINATION_ADDRESS = Address("UQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Send TON with optional text comment
    # destination: recipient address
    # amount: in nanotons (use to_nano() to convert from TON)
    #   1 TON = 1,000,000,000 nanotons (10^9)
    # body: optional text comment (visible in explorers and recipient wallet)
    msg = await wallet.transfer(
        destination=DESTINATION_ADDRESS,
        amount=to_nano(0.01),  # Convert 0.01 TON to nanotons (10,000,000)
        body="Hello from tonutils!",
    )

    # Normalized hash of the signed external message (computed locally before sending)
    # Not a blockchain transaction hash — use it to track whether the message
    # was accepted on-chain (e.g. via explorers, API queries, or your own checks)
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
