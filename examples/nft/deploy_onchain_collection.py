from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import CollectionStandard
from tonutils.nft.content import CollectionOnchainContent
from tonutils.nft.royalty_params import RoyaltyParams
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the owner of the NFT collection
OWNER_ADDRESS = "UQ..."

# Royalty parameters: base and factor for calculating the royalty
ROYALTY_BASE = 1000
ROYALTY_FACTOR = 55  # 5.5% royalty


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    collection = CollectionStandard(
        owner_address=Address(OWNER_ADDRESS),
        next_item_index=0,
        content=CollectionOnchainContent(
            name="Welcome to TON",
            description="Each digital artwork represents a memorable token",
            image_data=b'image data',
            social_links=["https://ton.org/", "https://t.me/toncoin", "https://twitter.com/ton_blockchain"],
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
