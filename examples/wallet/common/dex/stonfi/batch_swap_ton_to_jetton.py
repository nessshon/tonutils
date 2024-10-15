from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2
from tonutils.wallet.data import SwapTONToJettonData

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Mnemonic phrase for creating the wallet
MNEMONIC: list[str] = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_stonfi_swap_ton_to_jetton(
        data_list=[
            SwapTONToJettonData(
                jetton_master_address="EQ...",
                ton_amount=0.01,
            ),
            SwapTONToJettonData(
                jetton_master_address="EQ...",
                ton_amount=0.01,
            ),
            SwapTONToJettonData(
                jetton_master_address="EQ...",
                ton_amount=0.01,
            ),
            SwapTONToJettonData(
                jetton_master_address="EQ...",
                ton_amount=0.01,
            ),
        ]
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
