from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import CollectionEditable, NFTEditable
from tonutils.nft.content import NFTOnchainContent
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


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    nft = NFTEditable(
        index=NFT_INDEX,
        collection_address=Address(COLLECTION_ADDRESS),
    )
    body = CollectionEditable.build_mint_body(
        index=NFT_INDEX,
        owner_address=Address(OWNER_ADDRESS),
        content=NFTOnchainContent(
            name="TON Collectible #0",
            description="Memorable token for completing an onboarding quest about the TON ecosystem",
            image_data=b'image data',
        ),
    )

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
