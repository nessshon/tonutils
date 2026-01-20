from pytoniq_core import Address

from tonutils.clients import ToncenterClient
from tonutils.contracts import (
    NFTCollectionStandard,
    NFTCollectionData,
    NFTItemStandard,
    NFTCollectionContent,
    OffchainContent,
    OffchainCommonContent,
    RoyaltyParams,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Collection owner address (controls collection)
OWNER_ADDRESS = Address("UQ...")

# Collection metadata URI (TEP-64 off-chain format)
# Points to JSON with collection-level metadata (name, description, image)
COLLECTION_URI = "https://example.com/collection.json"

# Common prefix for individual NFT item metadata URIs
# Collection appends item-specific suffix (e.g., "0.json", "1.json")
# Full item URI = ITEMS_PREFIX_URI + item_index + ".json"
ITEMS_PREFIX_URI = "https://example.com/items/"

# Royalty percentage in basis points (1/1000)
# 50 = 5% royalty (50/1000 = 0.05)
ROYALTY = 50
ROYALTY_DENOMINATOR = 1000

# Address to receive royalty payments on secondary sales
ROYALTY_ADDRESS = Address("UQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Get default NFT item code
    nft_item_code = NFTItemStandard.get_default_code()

    # Configure royalty parameters
    # royalty: numerator for royalty calculation
    # denominator: denominator for royalty calculation
    #   Royalty share = royalty / denominator (e.g., 50/1000 = 5%)
    # address: destination for royalty payments on secondary sales
    royalty_params = RoyaltyParams(
        royalty=ROYALTY,
        denominator=ROYALTY_DENOMINATOR,
        address=ROYALTY_ADDRESS,
    )

    # Configure collection metadata
    # content: collection-level metadata URI (name, description, image)
    # common_content: prefix for individual item metadata URIs
    nft_collection_content = NFTCollectionContent(
        content=OffchainContent(uri=COLLECTION_URI),
        common_content=OffchainCommonContent(prefix_uri=ITEMS_PREFIX_URI),
    )

    # Compose collection initial data
    # owner_address: collection owner (can mint items)
    # content: collection and item metadata configuration
    # royalty_params: royalty configuration for secondary sales
    # nft_item_code: code cell used to deploy each NFT item
    nft_collection_data = NFTCollectionData(
        owner_address=OWNER_ADDRESS,
        content=nft_collection_content,
        royalty_params=royalty_params,
        nft_item_code=nft_item_code,
    )

    # Create collection contract instance from initial data
    # Generates collection address deterministically from code + data hash
    # Address is predictable before deployment (same data = same address)
    nft_collection = NFTCollectionStandard.from_data(
        client=client,
        data=nft_collection_data.serialize(),
    )

    # Deploy collection contract via state_init message
    # destination: collection address (derived from code + data)
    # amount: TON attached for deployment gas fees (0.05 TON typical)
    # state_init: initial code and data for contract deployment
    msg = await wallet.transfer(
        destination=nft_collection.address,
        amount=to_nano(0.05),
        state_init=nft_collection.state_init,
    )

    # Display deployed collection address
    print(f"NFT collection address: {nft_collection.address.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
