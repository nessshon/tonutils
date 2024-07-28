from tonutils.client import TonapiClient
from tonutils.wallet import HighloadWalletV2
from tonutils.wallet.data import TransferItemData

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = HighloadWalletV2.from_mnemonic(MNEMONIC, client)

    tx_hash = await wallet.transfer_nft(
        data_list=[
            TransferItemData(
                destination="UQ...",
                item_address="EQ...",
            ),
            TransferItemData(
                destination="UQ...",
                item_address="EQ...",
            ),
            TransferItemData(
                destination="UQ...",
                item_address="EQ...",
            ),
        ]
    )

    print("Successfully transferred!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
