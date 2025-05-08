from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStablecoin
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the Jetton Master contract where the admin will be changed
JETTON_MASTER_ADDRESS = "EQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = JettonMasterStablecoin.build_drop_admin_body()

    tx_hash = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        amount=0.05,
        body=body,
    )

    print(f"Jetton Master admin has been successfully dropped!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
