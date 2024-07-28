from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2
from tonutils.wallet.data import TransferData

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(MNEMONIC, client)

    tx_hash = await wallet.batch_transfer(
        data_list=[
            TransferData(
                destination="UQ...",
                amount=0.01,
                body="Hello from tonutils!",
            ),
            TransferData(
                destination="UQ...",
                amount=0.02,
                body="Hello from tonutils!",
            ),
            TransferData(
                destination="UQ...",
                amount=0.03,
                body="Hello from tonutils!",
            ),
            TransferData(
                destination="UQ...",
                amount=0.04,
                body="Hello from tonutils!",
            ),
        ]
    )

    print("Successfully transferred!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
