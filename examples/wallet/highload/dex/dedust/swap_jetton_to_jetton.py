from tonutils.client import TonapiClient
from tonutils.wallet import HighloadWalletV2
from tonutils.wallet.data import SwapJettonToJettonData

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Mnemonic phrase for creating the wallet
MNEMONIC: list[str] = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY)
    wallet, _, _, _ = HighloadWalletV2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_dedust_swap_jetton_to_jetton(
        data_list=[
            SwapJettonToJettonData(
                from_jetton_master_address="EQ...",
                to_jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            SwapJettonToJettonData(
                from_jetton_master_address="EQ...",
                to_jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            SwapJettonToJettonData(
                from_jetton_master_address="EQ...",
                to_jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            SwapJettonToJettonData(
                from_jetton_master_address="EQ...",
                to_jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
        ]
    )

    print("Successfully swapped Jetton to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
