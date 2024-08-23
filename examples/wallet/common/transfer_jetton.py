from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for the test network, False for the main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of Jettons to transfer (in base units, considering decimals)
JETTON_AMOUNT = 0.01

# The address of the recipient
DESTINATION_ADDRESS = "UQ..."

# Comment to include in the transfer payload
COMMENT = "Hello from tonutils!"


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.transfer_jetton(
        destination=DESTINATION_ADDRESS,
        jetton_master_address=JETTON_MASTER_ADDRESS,
        jetton_amount=JETTON_AMOUNT,
        jetton_decimals=JETTON_DECIMALS,
        forward_payload=COMMENT,
    )

    print(f"Successfully transferred {JETTON_AMOUNT} jettons!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
