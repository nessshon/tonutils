from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for the test network, False for the main network
IS_TESTNET = False

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"  # noqa
TO_JETTON_MASTER_ADDRESS = "EQAvlWFDxGF2lXm67y4yzC17wYKD9A0guwPkMs1gOsM__NOT"  # noqa

# Number of decimal places for the Jetton
FROM_JETTON_DECIMALS = 6
TO_JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.stonfi_swap_jetton_to_jetton(
        from_jetton_master_address=FROM_JETTON_MASTER_ADDRESS,
        to_jetton_master_address=TO_JETTON_MASTER_ADDRESS,
        jetton_amount=JETTON_AMOUNT,
        from_jetton_decimals=FROM_JETTON_DECIMALS,
        to_jetton_decimals=TO_JETTON_DECIMALS,
    )

    print("Successfully swapped Jetton to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
