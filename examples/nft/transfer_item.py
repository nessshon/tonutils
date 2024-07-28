import asyncio

from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import ItemStandard
from tonutils.wallet import WalletV4R2

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []

ITEM_ADDRESS = Address("EQBca66SemXdnpfi4bb2wStQGCAQ25RF-NqkMv6F6q0m-DIQ")  # noqa
NEW_OWNER_ADDRESS = Address("EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c")  # noqa


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(MNEMONIC, client)

    body = ItemStandard.build_transfer_body(
        new_owner_address=NEW_OWNER_ADDRESS,
    )

    # For item editable use:
    """
    body = ItemEditable.build_transfer_body(
        new_owner_address=NEW_OWNER_ADDRESS,
    )
    """

    tx_hash = await wallet.transfer(
        destination=ITEM_ADDRESS,
        amount=0.05,
        body=body,
    )

    print(f"Transferred item {ITEM_ADDRESS.to_str()} to {NEW_OWNER_ADDRESS.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    asyncio.run(main())
