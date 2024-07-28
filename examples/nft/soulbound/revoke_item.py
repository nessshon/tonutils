from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import ItemSoulbound
from tonutils.wallet import WalletV4R2

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []

ITEM_ADDRESS = Address("EQB6U56wUiIhPRrqH2fPmO_Oiv3pMOG7Yx0t3qng6MRkZefK")  # noqa


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(MNEMONIC, client)

    body = ItemSoulbound.build_revoke_body()

    tx_hash = await wallet.transfer(
        destination=ITEM_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Revoked item: {ITEM_ADDRESS.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
