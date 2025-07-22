from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft.content import SweetOffchainContent
from tonutils.nft.contract.standard.collection import SweetCollectionStandard
from tonutils.nft.contract.standard.nft import SweetNFTStandard
from tonutils.wallet import WalletV5R1

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet, should be minter or owner of the NFT collection
MNEMONIC: list[str] = []

# Address of the owner of the NFT and the NFT collection contract
OWNER_ADDRESS = ""
COLLECTION_ADDRESS = ""

# Suffix URI of the NFT metadata
METADATA_URI = f""


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV5R1.from_mnemonic(client, MNEMONIC)

    nft = SweetNFTStandard(
        collection_address=Address(COLLECTION_ADDRESS),
    )
    body = SweetCollectionStandard.build_mint_body(
        owner_address=Address(OWNER_ADDRESS),
        content=SweetOffchainContent(base_uri=METADATA_URI),
    )


    tx_hash = await wallet.transfer(
        destination=COLLECTION_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Successfully minted NFT from collection {nft.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
