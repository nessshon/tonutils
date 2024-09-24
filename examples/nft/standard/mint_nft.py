from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft.content import NFTOffchainContent
from tonutils.nft.contract.standard.collection import CollectionStandard
from tonutils.nft.contract.standard.nft import NFTStandard
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the owner of the NFT and the NFT collection contract
OWNER_ADDRESS = "UQ..."
COLLECTION_ADDRESS = "EQ..."

# Index of the NFT to be minted
NFT_INDEX = 0

# Suffix URI of the NFT metadata
SUFFIX_URI = f"{NFT_INDEX}.json"


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    nft = NFTStandard(
        index=NFT_INDEX,
        collection_address=Address(COLLECTION_ADDRESS),
    )
    body = CollectionStandard.build_mint_body(
        index=NFT_INDEX,
        owner_address=Address(OWNER_ADDRESS),
        content=NFTOffchainContent(suffix_uri=SUFFIX_URI),
    )

    """ If you deployed the collection using the Modified variant, replace the above code with:
        Replace `CollectionStandard` and `NFTStandard` with their modified versions,
        and use `NFTModifiedOffchainContent` to specify the full `URI` for the NFT metadata.

    Example:

    nft = NFTStandardModified(
        index=NFT_INDEX,
        collection_address=Address(COLLECTION_ADDRESS),
    )
    body = CollectionStandardModified.build_mint_body(
        index=NFT_INDEX,
        owner_address=Address(OWNER_ADDRESS),
        content=NFTModifiedOffchainContent(uri=URI),  # URI example: `https://example.com/nft/0.json`.
    )
    """

    tx_hash = await wallet.transfer(
        destination=COLLECTION_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Successfully minted NFT with index {NFT_INDEX}: {nft.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
