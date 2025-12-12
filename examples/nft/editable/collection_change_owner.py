from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    NFTCollectionChangeOwnerBody,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# New owner address
OWNER_ADDRESS = Address("UQ...")

# Deployed NFT collection contract address to transfer
NFT_COLLECTION_ADDRESS = Address("EQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be current collection owner to change ownership successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Construct change owner message body
    # owner_address: new owner address (receives collection control)
    body = NFTCollectionChangeOwnerBody(owner_address=OWNER_ADDRESS)

    # Send change owner transaction to collection contract
    # destination: collection contract address
    # body: serialized change owner message
    # amount: TON attached for gas fees (0.05 TON typical)
    msg = await wallet.transfer(
        destination=NFT_COLLECTION_ADDRESS,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    # Display NFT collection address with transferred ownership
    print(f"NFT collection address: {NFT_COLLECTION_ADDRESS.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
