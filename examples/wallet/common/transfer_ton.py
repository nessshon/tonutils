from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the recipient
DESTINATION_ADDRESS = "UQ..."

# Optional comment to include in the forward payload
COMMENT = "Hello from tonutils!"

# Amount to transfer in TON
AMOUNT = 0.01


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.transfer(
        destination=DESTINATION_ADDRESS,
        amount=AMOUNT,
        body=COMMENT,
    )

    print(f"Successfully transferred {AMOUNT} TON!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
