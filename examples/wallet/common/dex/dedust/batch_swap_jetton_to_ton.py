from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2
from tonutils.wallet.data import SwapJettonToTONData

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Mnemonic phrase for creating the wallet
MNEMONIC: list[str] = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_dedust_swap_jetton_to_ton(
        data_list=[
            SwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            SwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            SwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            SwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
        ]
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
