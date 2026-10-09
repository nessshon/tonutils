from ton_core import Address, NetworkGlobalID, to_nano

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV4R2

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

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Send TON with a comment encrypted end-to-end (ECDH) for the recipient
    # The recipient's public key is fetched via its get_public_key get-method;
    # for an undeployed recipient pass recipient_public_key explicitly
    msg = await wallet.transfer(
        destination=DESTINATION_ADDRESS,
        amount=to_nano(0.01),  # Convert 0.01 TON to nanotons (10,000,000)
        body="Hello from tonutils!",
        encrypt=True,
    )

    # Normalized hash of the signed external message (computed locally before sending)
    # Not a blockchain transaction hash — use it to track whether the message
    # was accepted on-chain (e.g. via explorers, API queries, or your own checks)
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
