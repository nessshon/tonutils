from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.nft import CollectionEditable
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the new owner to whom the collection ownership will be transferred
NEW_OWNER_ADDRESS = "UQ..."

# Address of the NFT collection whose ownership will be changed
COLLECTION_ADDRESS = "EQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = CollectionEditable.build_change_owner_body(
        owner_address=Address(NEW_OWNER_ADDRESS),
    )

    tx_hash = await wallet.transfer(
        destination=COLLECTION_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Successfully changed the owner of collection {COLLECTION_ADDRESS} to {NEW_OWNER_ADDRESS}.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
