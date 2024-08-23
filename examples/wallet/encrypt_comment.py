from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the recipient wallet
DESTINATION_ADDRESS = "UQ..."

# Amount to transfer in TON
TRANSFER_AMOUNT = 0.01

# Comment to include in the transfer payload
COMMENT = "Hello from tonutils!"


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = await wallet.build_encrypted_comment_body(
        text=COMMENT,
        destination=DESTINATION_ADDRESS,
    )

    tx_hash = await wallet.transfer(
        destination=DESTINATION_ADDRESS,
        amount=TRANSFER_AMOUNT,
        body=body,
    )

    print(f"Successfully transferred {TRANSFER_AMOUNT} TON to address {DESTINATION_ADDRESS}.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
