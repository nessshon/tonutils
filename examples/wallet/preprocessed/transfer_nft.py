from tonutils.client import TonapiClient
from tonutils.wallet import PreprocessedWalletV2
from tonutils.wallet.data import TransferNFTData

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase for creating the wallet
MNEMONIC: list[str] = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = PreprocessedWalletV2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_nft_transfer(
        data_list=[
            TransferNFTData(
                destination="UQ...",
                nft_address="EQ...",
            ),
            TransferNFTData(
                destination="UQ...",
                nft_address="EQ...",
            ),
            TransferNFTData(
                destination="UQ...",
                nft_address="EQ...",
            ),
            TransferNFTData(
                destination="UQ...",
                nft_address="EQ...",
            ),
        ]
    )

    print("Successfully transferred!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
