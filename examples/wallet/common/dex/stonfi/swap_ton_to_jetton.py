from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for the test network, False for the main network
IS_TESTNET = False

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the Jetton Master for swapping (TON > USD₮)
TO_JETTON_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"  # noqa

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of TON to swap (in TON)
SWAP_TON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.stonfi_swap_ton_to_jetton(
        jetton_master_address=TO_JETTON_MASTER_ADDRESS,
        ton_amount=SWAP_TON_AMOUNT,
        jetton_decimals=JETTON_DECIMALS,
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
