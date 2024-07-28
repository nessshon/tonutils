from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import CollectionStandard
from tonutils.nft.content import OffchainContent
from tonutils.nft.royalty_params import RoyaltyParams
from tonutils.wallet import WalletV4R2

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []

OWNER_ADDRESS = Address("EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess")  # noqa


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(MNEMONIC, client)

    collection = CollectionStandard(
            owner_address=OWNER_ADDRESS,
            next_item_index=0,
            content=OffchainContent(
                uri="https://nft.tonplanets.com/nft/colonizer/collection.json",
                suffix_uri="https://nft.tonplanets.com/nft/colonizer/",
            ),
            royalty_params=RoyaltyParams(
                base=1000,
                factor=55,  # 5.5% royalty
                address=OWNER_ADDRESS,
            ),
    )

    tx_hash = await wallet.transfer(
        destination=collection.address,
        amount=0.05,
        state_init=collection.state_init,
    )

    print(f"Deployed collection: {collection.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
