from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    NFTCollectionBatchMintItemBody,
    NFTCollectionEditable,
    NFTItemEditable,
    NFTItemEditableMintRef,
    OffchainItemContent,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."

MINT_FROM_INDEX = 0
NFT_ITEM_OWNERS_AND_EDITORS = [
    (Address("UQ..."), Address("UQ...")),
    (Address("UQ..."), Address("UQ...")),
    (Address("UQ..."), Address("UQ...")),
]
NFT_COLLECTION_ADDRESS = Address("EQ...")


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    nft_item_code = NFTItemEditable.get_default_code()
    nft_items_count = len(NFT_ITEM_OWNERS_AND_EDITORS)
    nft_items_refs = []

    for nft_item_index, (owner_address, editor_address) in enumerate(
        NFT_ITEM_OWNERS_AND_EDITORS, start=MINT_FROM_INDEX
    ):
        nft_item_ref = NFTItemEditableMintRef(
            owner_address=owner_address,
            editor_address=editor_address,
            content=OffchainItemContent(prefix_uri=f"{nft_item_index}.json"),
        )
        nft_items_refs.append(nft_item_ref.serialize())

    body = NFTCollectionBatchMintItemBody(
        items_refs=nft_items_refs,
        from_index=MINT_FROM_INDEX,
        forward_amount=to_nano(0.01),
    )

    msg = await wallet.transfer(
        destination=NFT_COLLECTION_ADDRESS,
        amount=to_nano(0.25) * nft_items_count,
        body=body.serialize(),
    )

    for nft_item_index in range(MINT_FROM_INDEX, MINT_FROM_INDEX + nft_items_count):
        nft_item_address = NFTCollectionEditable.calculate_nft_item_address(
            index=nft_item_index,
            nft_item_code=nft_item_code,
            collection_address=NFT_COLLECTION_ADDRESS,
        )
        print(f"[{nft_item_index}] NFT item address: {nft_item_address.to_str()}")

    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
