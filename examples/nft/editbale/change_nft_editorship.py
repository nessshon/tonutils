from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.nft import NFTEditable
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the NFT whose editorship will be changed
NFT_ADDRESS = "EQ..."

# Address of the new editor to whom the editorship will be transferred
NEW_EDITOR_ADDRESS = "UQ..."


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = NFTEditable.build_change_editorship_body(
        editor_address=Address(NEW_EDITOR_ADDRESS),
    )

    tx_hash = await wallet.transfer(
        destination=NFT_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Successfully changed the editorship of NFT {NFT_ADDRESS} to {NEW_EDITOR_ADDRESS}.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
