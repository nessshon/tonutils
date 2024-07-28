from tonutils.client import TonapiClient
from tonutils.wallet import HighloadWalletV2
from tonutils.wallet.data import TransferJettonData

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = HighloadWalletV2.from_mnemonic(MNEMONIC, client)

    tx_hash = await wallet.transfer_jetton(
        data_list=[
            TransferJettonData(
                destination="UQ...",
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                forward_payload="Hello from tonutils!"
            ),
            TransferJettonData(
                destination="UQ...",
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                forward_payload="Hello from tonutils!"
            ),
            TransferJettonData(
                destination="UQ...",
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                forward_payload="Hello from tonutils!"
            )
        ]
    )

    print("Successfully transferred!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
