from ton_core import (
    Address,
    NetworkGlobalID,
    NFTCollectionChangeContentBody,
    NFTCollectionContent,
    OffchainCommonContent,
    OffchainContent,
    RoyaltyParams,
    to_nano,
)

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV4R2

# Mnemonic phrase — 24 words (TON-native) or 12/18/24 words (BIP-39 import)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Collection owner address
OWNER_ADDRESS = Address("UQ...")

# Deployed NFT collection contract address to update
NFT_COLLECTION_ADDRESS = Address("EQ...")

# New collection metadata URI (TEP-64 off-chain format)
# Points to JSON with updated collection-level metadata (name, description, image)
COLLECTION_URI = "https://example.com/collection.json"

# New common prefix for individual NFT item metadata URIs
# Collection appends item-specific suffix (e.g., "0.json", "1.json")
# Full item URI = ITEMS_PREFIX_URI + item_index + ".json"
ITEMS_PREFIX_URI = "https://example.com/items/"

# Royalty numerator for fraction: numerator / denominator
# 50 / 1000 = 5% royalty
ROYALTY = 50
ROYALTY_DENOMINATOR = 1000

# New address to receive royalty payments on secondary sales
ROYALTY_ADDRESS = Address("UQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be collection owner to change content successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Configure new royalty parameters
    # royalty: numerator for royalty calculation
    # denominator: denominator for royalty calculation
    #   Royalty share = royalty / denominator (e.g., 50/1000 = 5%)
    # address: destination for royalty payments on secondary sales
    royalty_params = RoyaltyParams(
        royalty=ROYALTY,
        denominator=ROYALTY_DENOMINATOR,
        address=ROYALTY_ADDRESS,
    )

    # Configure new collection metadata
    # content: updated collection-level metadata URI (name, description, image)
    # common_content: updated prefix for individual item metadata URIs
    nft_collection_content = NFTCollectionContent(
        content=OffchainContent(uri=COLLECTION_URI),
        common_content=OffchainCommonContent(prefix_uri=ITEMS_PREFIX_URI),
    )

    # Construct change content message body
    # content: new collection metadata configuration
    # royalty_params: new royalty configuration for secondary sales
    body = NFTCollectionChangeContentBody(
        content=nft_collection_content,
        royalty_params=royalty_params,
    )

    # Send change content transaction to collection contract
    # destination: collection contract address
    # body: serialized change content message
    # amount: TON attached for gas fees (0.05 TON typical)
    msg = await wallet.transfer(
        destination=NFT_COLLECTION_ADDRESS,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    # Display updated NFT collection address
    print(f"NFT collection address: {NFT_COLLECTION_ADDRESS.to_str()}")

    # Normalized hash of the signed external message (computed locally before sending)
    # Not a blockchain transaction hash — use it to track whether the message
    # was accepted on-chain (e.g. via explorers, API queries, or your own checks)
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
