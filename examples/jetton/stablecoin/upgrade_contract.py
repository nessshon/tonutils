from pytoniq_core import Cell

from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStablecoin
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# Cell containing the updated contract code
NEW_CODE_CELL = Cell.one_from_boc("code hex")

# Cell containing the updated contract data
NEW_DATA_CELL = Cell.one_from_boc("data hex")


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
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
