from tonutils.client import ToncenterV3Client
from tonutils.nft import NFTEditable
from tonutils.nft.content import NFTOffchainContent
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the NFT to be edited
NFT_ADDRESS = "EQ..."

# Suffix URI of the NFT metadata
SUFFIX_URI = f"new-content.json"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = NFTEditable.build_edit_content_body(
        content=NFTOffchainContent(suffix_uri=SUFFIX_URI),
    )

    tx_hash = await wallet.transfer(
        destination=NFT_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Successfully edited the content of NFT at address: {NFT_ADDRESS}.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
