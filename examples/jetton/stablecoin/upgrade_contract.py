from pytoniq_core import Cell

from tonutils.client import TonapiClient
from tonutils.jetton import JettonMasterStablecoin
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# Cell containing the updated contract code
NEW_CODE_CELL = Cell.one_from_boc("code hex")

# Cell containing the updated contract data
NEW_DATA_CELL = Cell.one_from_boc("data hex")


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = JettonMasterStablecoin.build_upgrade_message_body(
        new_code=NEW_CODE_CELL,
        new_data=NEW_DATA_CELL,
    )

    tx_hash = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        amount=0.05,
        body=body,
    )

    print(f"Successfully upgraded the contract!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
