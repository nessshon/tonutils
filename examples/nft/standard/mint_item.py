from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    NFTCollectionStandard,
    NFTCollectionMintItemBody,
    NFTItemStandard,
    NFTItemStandardMintRef,
    OffchainItemContent,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# NFT item owner address (receives minted NFT)
OWNER_ADDRESS = Address("UQ...")

# Deployed NFT collection contract address
NFT_COLLECTION_ADDRESS = Address("EQ...")

# Unique index for NFT item within collection
# Sequential numbering: 0, 1, 2, ... (increments with each mint)
NFT_ITEM_INDEX = 0

# Metadata suffix appended to collection's ITEMS_PREFIX_URI
# Full metadata URI = collection.common_content.prefix_uri + suffix_uri
# Example: if prefix is "https://example.com/items/", suffix "0.json" → "https://example.com/items/0.json"
NFT_ITEM_SUFFIX_URI = f"0.json"


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be collection owner to mint successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Get default NFT item code
    nft_item_code = NFTItemStandard.get_default_code()

    # Create off-chain content structure
    # suffix_uri: appended to collection's base URI to form full metadata URL
    nft_item_content = OffchainItemContent(suffix_uri=NFT_ITEM_SUFFIX_URI)

    # Build NFT item initialization data (stored in item contract on deployment)
    # owner_address: initial owner of the NFT item
    # content: item-specific metadata (suffix for off-chain content)
    nft_item_ref = NFTItemStandardMintRef(
        owner_address=OWNER_ADDRESS,
        content=nft_item_content,
    )

    # Construct mint message body
    # item_index: unique index within collection (used for address calculation)
    # item_ref: serialized initialization data (owner + content)
    # forward_amount: nanotons forwarded to newly deployed item (covers initial storage fees)
    #   Typical: 0.01 TON ensures item has balance for storage rent
    body = NFTCollectionMintItemBody(
        item_index=NFT_ITEM_INDEX,
        item_ref=nft_item_ref.serialize(),
        forward_amount=to_nano(0.01),
    )

    # Send mint transaction to collection contract
    # destination: collection contract address
    # amount: TON attached to message (covers gas + forward_amount)
    #   Must be >= forward_amount + gas fees (typical: 0.025 TON total)
    # body: serialized mint message
    msg = await wallet.transfer(
        destination=NFT_COLLECTION_ADDRESS,
        amount=to_nano(0.025),
        body=body.serialize(),
    )

    # Calculate NFT item address deterministically
    # Derived from: item_index + nft_item_code + collection_address
    # Address predictable before deployment (same inputs = same address)
    nft_item_address = NFTCollectionStandard.calculate_nft_item_address(
        index=NFT_ITEM_INDEX,
        nft_item_code=nft_item_code,
        collection_address=NFT_COLLECTION_ADDRESS,
    )

    # Display minted NFT item address
    print(f"NFT item address: {nft_item_address.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
