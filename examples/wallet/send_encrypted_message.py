from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the recipient wallet
DESTINATION_ADDRESS = "UQ..."

# Amount to transfer in TON
TRANSFER_AMOUNT = 0.01

# Comment to include in the transfer payload
COMMENT = "Hello from tonutils!"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
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
