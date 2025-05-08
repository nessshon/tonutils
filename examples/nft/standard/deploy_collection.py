from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.nft import CollectionStandard
from tonutils.nft.content import CollectionOffchainContent
from tonutils.nft.royalty_params import RoyaltyParams
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the owner of the NFT collection
OWNER_ADDRESS = "UQ..."

# URI of the collection's metadata
# https://github.com/ton-blockchain/TEPs/blob/master/text/0064-token-data-standard.md#nft-collection-metadata-example-offchain
URI = "https://example.com/nft/collection.json"
PREFIX_URI = "https://example.com/nft/"

# Royalty parameters: base and factor for calculating the royalty
ROYALTY_BASE = 1000
ROYALTY_FACTOR = 55  # 5.5% royalty


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    collection = CollectionStandard(
        owner_address=Address(OWNER_ADDRESS),
        next_item_index=0,
        content=CollectionOffchainContent(uri=URI, prefix_uri=PREFIX_URI),
        royalty_params=RoyaltyParams(
            base=ROYALTY_BASE,
            factor=ROYALTY_FACTOR,
            address=Address(OWNER_ADDRESS),
        ),
    )

    """ If you want the option to withdraw extra balance in the future and store collection and NFT data on-chain,
        you can use `CollectionStandardModified`. It removes the need for `prefix_uri` because NFTs minted in this
        format include a direct link to the metadata for each item, rather than using a shared prefix for all items.

    Example:

    collection = CollectionStandardModified(
        owner_address=Address(OWNER_ADDRESS),
        next_item_index=0,
        content=CollectionModifiedOffchainContent(uri=URI),  # URI example: `https://example.com/nft/collection.json`.
        royalty_params=RoyaltyParams(
            base=ROYALTY_BASE,
            factor=ROYALTY_FACTOR,
            address=Address(OWNER_ADDRESS),
        ),
    )
    """

    tx_hash = await wallet.transfer(
        destination=collection.address,
        amount=0.05,
        state_init=collection.state_init,
    )

    print(f"Successfully deployed NFT Collection at address: {collection.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
