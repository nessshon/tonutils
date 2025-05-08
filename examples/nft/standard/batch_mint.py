from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.nft import CollectionStandard
from tonutils.nft.content import NFTOffchainContent
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the owner of the NFT and the NFT collection contract
OWNER_ADDRESS = "UQ..."
COLLECTION_ADDRESS = "EQ..."

# Starting index for minting items
FROM_INDEX = 0

# Number of items to mint
ITEMS_COUNT = 100


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = CollectionStandard.build_batch_mint_body(
        data=[
            (
                NFTOffchainContent(suffix_uri=f"{index}.json"),
                Address(OWNER_ADDRESS),
            )
            for index in range(FROM_INDEX, FROM_INDEX + ITEMS_COUNT)
        ],
        from_index=FROM_INDEX,
    )

    """ If you deployed the collection using the Modified variant, replace the above code with:
        Replace `CollectionStandard` with `CollectionStandardModified`, 
        and use `NFTModifiedOffchainContent` to specify the full `URI` for each NFT metadata.

    Example:

    body = CollectionStandardModified.build_batch_mint_body(
        data=[
            (
                NFTModifiedOffchainContent(uri=URI),  # URI example: `https://example.com/nft/{index}.json`.
                Address(OWNER_ADDRESS),
            )
            for index in range(FROM_INDEX, FROM_INDEX + ITEMS_COUNT)
        ],
        from_index=FROM_INDEX,
    )
    """

    tx_hash = await wallet.transfer(
        destination=COLLECTION_ADDRESS,
        amount=ITEMS_COUNT * 0.05,
        body=body,
    )

    print(f"Successfully minted {ITEMS_COUNT} items in the collection at address: {COLLECTION_ADDRESS}.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
