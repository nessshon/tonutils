from tonutils.client import ToncenterV3Client
from tonutils.wallet import PreprocessedWalletV2R1
from tonutils.wallet.data import TransferData

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = PreprocessedWalletV2R1.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_transfer(
        data_list=[
            TransferData(
                destination="UQ...",
                amount=0.01,
                body="Hello from tonutils!",
            ),
            TransferData(
                destination="UQ...",
                amount=0.01,
                body="Hello from tonutils!",
            ),
            TransferData(
                destination="UQ...",
                amount=0.01,
                body="Hello from tonutils!",
            ),
            TransferData(
                destination="UQ...",
                amount=0.01,
                body="Hello from tonutils!",
            ),
        ]
    )

    print("Successfully transferred!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
