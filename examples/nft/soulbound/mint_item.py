from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import CollectionSoulbound, ItemSoulbound
from tonutils.nft.content import OffchainCommonContent
from tonutils.wallet import WalletV4R2

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []

OWNER_ADDRESS = Address("EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess")  # noqa
COLLECTION_ADDRESS = Address("EQC5FNhcIyExh-fmu6EZSpd4L63M6B3JuMgeVhPnlZDNBhD_")  # noqa


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(MNEMONIC, client)

    index = 0

    item = ItemSoulbound(
        index=index,
        collection_address=COLLECTION_ADDRESS,
    )

    body = CollectionSoulbound.build_mint_body(
        index=index,
        owner_address=OWNER_ADDRESS,
        content=OffchainCommonContent(
            uri=f"{index}.json"
        ),
    )

    tx_hash = await wallet.transfer(
        destination=COLLECTION_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Minted item: {item.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
