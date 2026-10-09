from ton_core import Address, NetworkGlobalID, to_nano

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletTg

# Address of the existing wallet to open
WALLET_ADDRESS = Address("UQ...")

# Mnemonic phrase — TON or Multichain (BIP-39)
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

    # Open the wallet by its address with the current mnemonic
    # Unlike from_mnemonic (which derives the address from the key), this binds
    # the key to a known address and verifies the key actually controls it —
    # required for a wallet whose key was rotated away from the original mnemonic
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = await WalletTg.from_address_and_mnemonic(client, WALLET_ADDRESS, MNEMONIC)

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
