from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.jetton import JettonMasterStandard
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the Jetton Master contract where the admin will be changed
JETTON_MASTER_ADDRESS = "EQ..."

# The new administrator address to be set for the Jetton Master contract
NEW_ADMIN_ADDRESS = "UQ..."


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = JettonMasterStandard.build_change_admin_body(
        new_admin_address=Address(NEW_ADMIN_ADDRESS),
    )

    tx_hash = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        amount=0.05,
        body=body,
    )

    print(f"Successfully changed the admin of the Jetton Master!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
