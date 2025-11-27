from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    NFTCollectionMintItemBody,
    NFTCollectionStandard,
    NFTItemSoulbound,
    NFTItemSoulboundMintRef,
    OffchainItemContent,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."

OWNER_ADDRESS = Address("UQ...")
AUTHORITY_ADDRESS = Address("UQ...")
NFT_COLLECTION_ADDRESS = Address("EQ...")

NFT_ITEM_INDEX = 0
NFT_ITEM_PREFIX_URI = f"0.json"


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    nft_item_code = NFTItemSoulbound.get_default_code()
    nft_item_content = OffchainItemContent(prefix_uri=NFT_ITEM_PREFIX_URI)

    nft_item_ref = NFTItemSoulboundMintRef(
        owner_address=OWNER_ADDRESS,
        authority_address=AUTHORITY_ADDRESS,
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

    nft_item_address = NFTCollectionStandard.calculate_nft_item_address(
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
