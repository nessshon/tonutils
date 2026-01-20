from pytoniq_core import Address

from tonutils.clients import ToncenterClient
from tonutils.contracts import (
    NFTEditContentBody,
    OffchainItemContent,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Editable NFT item address to update
NFT_ITEM_ADDRESS = Address("EQ...")

# New metadata suffix appended to collection's ITEMS_PREFIX_URI
# Full metadata URI = collection.common_content.prefix_uri + suffix_uri
# Example: if prefix is "https://example.com/items/", suffix "0.json" → "https://example.com/items/0.json"
SUFFIX_URI = "0.json"


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be editor address to edit content successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Create new off-chain content structure
    # suffix_uri: new suffix appended to collection's base URI to form updated metadata URL
    nft_item_content = OffchainItemContent(suffix_uri=SUFFIX_URI)

    # Construct edit content message body
    # content: new item metadata configuration (updated suffix)
    body = NFTEditContentBody(content=nft_item_content)

    # Send edit content transaction to Editable NFT item contract
    # destination: Editable NFT item contract address
    # body: serialized edit content message
    # amount: TON attached for gas fees (0.05 TON typical)
    msg = await wallet.transfer(
        destination=NFT_ITEM_ADDRESS,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    # Display updated Editable NFT item address
    print(f"NFT item address: {NFT_ITEM_ADDRESS.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
