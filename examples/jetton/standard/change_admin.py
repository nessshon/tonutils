from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStandard
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the Jetton Master contract where the admin will be changed
JETTON_MASTER_ADDRESS = "EQ..."

# The new administrator address to be set for the Jetton Master contract
NEW_ADMIN_ADDRESS = "UQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = JettonMasterStandard.build_change_admin_body(
        new_admin_address=Address(NEW_ADMIN_ADDRESS),
    )

    tx_hash = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        amount=0.05,
        body=body,
    )

    print("Successfully changed the admin of the Jetton Master!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
