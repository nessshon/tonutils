from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import ItemEditable
from tonutils.wallet import WalletV4R2

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []

ITEM_ADDRESS = Address("EQAewY1hMNynw4H1dghwDdtr-qe_nnYH3M3cVHpCSfiDb8kY")  # noqa
NEW_EDITOR_ADDRESS = Address("EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c")  # noqa


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(MNEMONIC, client)

    body = ItemEditable.build_change_editorship_body(
        editor_address=NEW_EDITOR_ADDRESS,
    )

    tx_hash = await wallet.transfer(
        destination=ITEM_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Changed editorship of item {ITEM_ADDRESS.to_str()} to {NEW_EDITOR_ADDRESS.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
