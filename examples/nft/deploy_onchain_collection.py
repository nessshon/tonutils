from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.nft import CollectionEditableModified
from tonutils.nft.content import CollectionModifiedOnchainContent
from tonutils.nft.royalty_params import RoyaltyParams
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the owner of the NFT collection
OWNER_ADDRESS = "UQ..."

# Royalty parameters: base and factor for calculating the royalty
ROYALTY_BASE = 1000
ROYALTY_FACTOR = 55  # 5.5% royalty


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    collection = CollectionEditableModified(
        owner_address=Address(OWNER_ADDRESS),
        next_item_index=0,
        content=CollectionModifiedOnchainContent(
            name="Welcome to TON",
            description="Each digital artwork represents a memorable token",
            image_data=b'image data',
        ),
        royalty_params=RoyaltyParams(
            base=ROYALTY_BASE,
            factor=ROYALTY_FACTOR,
            address=Address(OWNER_ADDRESS),
        ),
    )

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
