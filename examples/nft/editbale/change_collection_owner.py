
from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import CollectionEditable
from tonutils.wallet import WalletV4R2

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []

OWNER_ADDRESS = Address("EQC-3ilVr-W0Uc3pLrGJElwSaFxvhXXfkiQA3EwdVBHNNess")  # noqa
COLLECTION_ADDRESS = Address("EQCulhVWqLmr29muYr-wNM7QvcLiP11E_XzbnMZTPeeU99Fv")  # noqa
NEW_OWNER_ADDRESS = Address("EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c")  # noqa


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(MNEMONIC, client)

    body = CollectionEditable.build_change_owner_body(
        owner_address=NEW_OWNER_ADDRESS,
    )

    tx_hash = await wallet.transfer(
        destination=COLLECTION_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Changed owner of collection: {COLLECTION_ADDRESS.to_str()} to {NEW_OWNER_ADDRESS.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
