from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2
from tonutils.wallet.data import TransferJettonData

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(MNEMONIC, client)

    tx_hash = await wallet.batch_jetton_transfer(
        data_list=[
            TransferJettonData(
                destination="UQ...",
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                forward_payload="Hello from tonutils!",
            ),
            TransferJettonData(
                destination="UQ...",
                jetton_master_address="EQ...",
                jetton_amount=0.02,
                forward_payload="Hello from tonutils!",
            ),
            TransferJettonData(
                destination="UQ...",
                jetton_master_address="EQ...",
                jetton_amount=0.03,
                forward_payload="Hello from tonutils!",
            ),
            TransferJettonData(
                destination="UQ...",
                jetton_master_address="EQ...",
                jetton_amount=0.04,
                forward_payload="Hello from tonutils!",
            ),
        ]
    )

    print("Successfully transferred!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
