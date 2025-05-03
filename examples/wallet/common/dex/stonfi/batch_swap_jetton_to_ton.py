from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2
from tonutils.wallet.data import StonfiSwapJettonToTONData

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for the test network, False for the main network
IS_TESTNET = False

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_stonfi_swap_jetton_to_ton(
        data_list=[
            StonfiSwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            StonfiSwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            StonfiSwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            StonfiSwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
        ],
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
