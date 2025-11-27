from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    NFTCollectionEditable,
    NFTCollectionMintItemBody,
    NFTItemEditable,
    NFTItemEditableMintRef,
    OffchainItemContent,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."

OWNER_ADDRESS = Address("UQ...")
EDITOR_ADDRESS = Address("UQ...")
NFT_COLLECTION_ADDRESS = Address("EQ...")

NFT_ITEM_INDEX = 0
NFT_ITEM_PREFIX_URI = f"{NFT_ITEM_INDEX}.json"


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    nft_item_code = NFTItemEditable.get_default_code()
    nft_item_content = OffchainItemContent(prefix_uri=NFT_ITEM_PREFIX_URI)

    nft_item_ref = NFTItemEditableMintRef(
        owner_address=OWNER_ADDRESS,
        editor_address=EDITOR_ADDRESS,
        content=nft_item_content,
    )
    body = NFTCollectionMintItemBody(
        item_index=NFT_ITEM_INDEX,
        item_ref=nft_item_ref.serialize(),
        forward_amount=to_nano(0.01),
    )

    msg = await wallet.transfer(
        destination=NFT_COLLECTION_ADDRESS,
        amount=to_nano(0.025),
        body=body.serialize(),
    )

    nft_item_address = NFTCollectionEditable.calculate_nft_item_address(
        index=NFT_ITEM_INDEX,
        nft_item_code=nft_item_code,
        collection_address=NFT_COLLECTION_ADDRESS,
    )

    print(f"NFT item address: {nft_item_address.to_str()}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
