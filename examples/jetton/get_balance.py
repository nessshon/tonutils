from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStandard, JettonWalletStandard
from tonutils.utils import to_amount

# Set to True for test network, False for main network
IS_TESTNET = True

# The address of the owner of the Jetton wallet
OWNER_ADDRESS = "UQ..."

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)

    jetton_wallet_address = await JettonMasterStandard.get_wallet_address(
        client=client,
        owner_address=OWNER_ADDRESS,
        jetton_master_address=JETTON_MASTER_ADDRESS,
    )

    jetton_wallet_data = await JettonWalletStandard.get_wallet_data(
        client=client,
        jetton_wallet_address=jetton_wallet_address,
    )

    print(f"Jetton wallet balance (nano): {jetton_wallet_data.balance}")
    print(f"Jetton wallet balance (Jettons): {to_amount(jetton_wallet_data.balance, JETTON_DECIMALS)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
