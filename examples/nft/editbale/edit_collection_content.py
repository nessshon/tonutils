from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import CollectionEditable
from tonutils.nft.content import CollectionOffchainContent
from tonutils.nft.royalty_params import RoyaltyParams
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the royalty receiver and the NFT collection contract
ROYALTY_ADDRESS = "UQ..."
COLLECTION_ADDRESS = "EQ..."

# URI of the collection's metadata
# https://github.com/ton-blockchain/TEPs/blob/master/text/0064-token-data-standard.md#nft-collection-metadata-example-offchain
URI = "https://example.com/collection.json"

# Royalty parameters: base and factor for calculating the royalty
ROYALTY_BASE = 1000
ROYALTY_FACTOR = 60  # 6% royalty


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = CollectionEditable.build_edit_content_body(
        content=CollectionOffchainContent(uri=URI),
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
