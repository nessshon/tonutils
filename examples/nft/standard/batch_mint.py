from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import CollectionStandard
from tonutils.nft.content import OffchainCommonContent
from tonutils.wallet import WalletV4R2

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []

OWNER_ADDRESS = Address("EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess")  # noqa
COLLECTION_ADDRESS = Address("EQBkBF5qLV0dmSR5LGH3VEjwiLAPW-ESiF7zOSDL8UUcdWW-")  # noqa


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(MNEMONIC, client)

    from_index = 0
    items_count = 100

    body = CollectionStandard.build_batch_mint_body(
        data=[
            (
                OffchainCommonContent(
                    uri=f"{index}.json"
                ),
                OWNER_ADDRESS,
            ) for index in range(from_index, items_count)
        ],
        from_index=from_index,
    )

    tx_hash = await wallet.transfer(
        destination=COLLECTION_ADDRESS,
        amount=items_count * 0.035,
        body=body,
    )

    print(f"Minted {items_count} items in collection {COLLECTION_ADDRESS.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
