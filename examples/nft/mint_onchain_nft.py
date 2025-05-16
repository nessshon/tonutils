from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.nft import CollectionEditableModified, NFTEditableModified
from tonutils.nft.content import NFTModifiedOnchainContent
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the owner of the NFT and the NFT collection contract
OWNER_ADDRESS = "UQ..."
COLLECTION_ADDRESS = "EQ..."

# Index of the NFT to be minted
NFT_INDEX = 0


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    nft = NFTEditableModified(
        index=NFT_INDEX,
        collection_address=Address(COLLECTION_ADDRESS),
    )
    body = CollectionEditableModified.build_mint_body(
        index=NFT_INDEX,
        owner_address=Address(OWNER_ADDRESS),
        content=NFTModifiedOnchainContent(
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
