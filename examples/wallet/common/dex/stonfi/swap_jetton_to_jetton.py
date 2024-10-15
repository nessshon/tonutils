from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Mnemonic phrase for creating the wallet
MNEMONIC: list[str] = []

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQ..."
TO_JETTON_MASTER_B_ADDRESS = "EQ..."

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.stonfi_swap_jetton_to_jetton(
        from_jetton_master_address=FROM_JETTON_MASTER_ADDRESS,
        to_jetton_master_address=TO_JETTON_MASTER_B_ADDRESS,
        jetton_amount=JETTON_AMOUNT,
        jetton_decimals=JETTON_DECIMALS,
    )

    print("Successfully swapped Jetton to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
