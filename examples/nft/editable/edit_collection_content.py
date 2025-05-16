from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.nft import CollectionEditable
from tonutils.nft.content import CollectionOffchainContent
from tonutils.nft.royalty_params import RoyaltyParams
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the royalty receiver and the NFT collection contract
ROYALTY_ADDRESS = "UQ..."
COLLECTION_ADDRESS = "EQ..."

# URI of the collection's metadata
# https://github.com/ton-blockchain/TEPs/blob/master/text/0064-token-data-standard.md#nft-collection-metadata-example-offchain
URI = "https://example.com/nft/collection.json"
PREFIX_URI = "https://example.com/nft/"

# Royalty parameters: base and factor for calculating the royalty
ROYALTY_BASE = 1000
ROYALTY_FACTOR = 60  # 6% royalty


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = CollectionEditable.build_edit_content_body(
        content=CollectionOffchainContent(uri=URI, prefix_uri=PREFIX_URI),
        royalty_params=RoyaltyParams(
            base=ROYALTY_BASE,
            factor=ROYALTY_FACTOR,
            address=Address(ROYALTY_ADDRESS),
        ),
    )

    tx_hash = await wallet.transfer(
        destination=COLLECTION_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Successfully edited the collection at address: {COLLECTION_ADDRESS}.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
