from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.nft import CollectionEditable
from tonutils.nft.content import NFTOffchainContent
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the owner and editor of the NFT and the NFT collection contract
OWNER_ADDRESS = "UQ..."
EDITOR_ADDRESS = "UQ..."
COLLECTION_ADDRESS = "EQ..."

# Starting index for minting items
FROM_INDEX = 0

# Number of items to mint
ITEMS_COUNT = 100


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = CollectionEditable.build_batch_mint_body(
        data=[
            (
                NFTOffchainContent(suffix_uri=f"{index}.json"),
                Address(OWNER_ADDRESS),
                Address(EDITOR_ADDRESS),
            )
            for index in range(FROM_INDEX, FROM_INDEX + ITEMS_COUNT)
        ],
        from_index=FROM_INDEX,
    )

    """ If you deployed the collection using the Modified variant, replace the above code with:
        Replace `CollectionEditable` with `CollectionEditableModified`, 
        and use `NFTModifiedOffchainContent` to specify the full `URI` for each NFT metadata.

    Example:

    body = CollectionEditableModified.build_batch_mint_body(
        data=[
            (
                NFTModifiedOffchainContent(uri=URI),  # URI example: `https://example.com/nft/{index}.json`.
                Address(OWNER_ADDRESS),
                Address(EDITOR_ADDRESS),
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

    print(f"Minted {ITEMS_COUNT} items in collection {COLLECTION_ADDRESS}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
