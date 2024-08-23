from tonutils.client import TonapiClient
from tonutils.nft.marketplace.getgems.contract.salev3r3 import SaleV3R3
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the sale contract
SALE_ADDRESS = "EQ..."


async def main() -> None:
    client = TonapiClient(API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SaleV3R3.build_cancel_sale_body()

    tx_hash = await wallet.transfer(
        destination=SALE_ADDRESS,
        amount=0.2,
        body=body,
    )

    print("Sale has been successfully canceled.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
