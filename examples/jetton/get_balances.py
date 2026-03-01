from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStandard, JettonWalletStandard
from tonutils.utils import to_amount

# Set to True for test network, False for main network
IS_TESTNET = True

# The address of the owner of the Jetton wallet
OWNER_ADDRESS = "UQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)

    jetton_infos = await client.get_jetton_wallets(owner_address=OWNER_ADDRESS)

    for wallet in jetton_infos.jetton_wallets:
        print(f"Jetton: {wallet.jetton}, Balance: {wallet.balance}, Owner: {wallet.owner}")



if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
