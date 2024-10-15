from tonutils.client import TonapiClient
from tonutils.jetton import JettonMaster
from tonutils.jetton.dex.stonfi import StonfiRouterV1
from tonutils.jetton.dex.stonfi.addresses import *
from tonutils.utils import to_nano
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for the test network, False for the main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQ..."
TO_JETTON_MASTER_ADDRESS = "EQ..."

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    router_address = TESTNET_V1_ROUTER_ADDRESS if IS_TESTNET else V1_ROUTER_ADDRESS

    offer_address = await JettonMaster.get_wallet_address(
        client=client,
        owner_address=wallet.address,
        jetton_master_address=FROM_JETTON_MASTER_ADDRESS,
    )
    ask_jetton_wallet_address = await JettonMaster.get_wallet_address(
        client=wallet.client,
        owner_address=router_address,
        jetton_master_address=TO_JETTON_MASTER_ADDRESS,
    )

    body = StonfiRouterV1.build_swap_body(
        jetton_amount=to_nano(JETTON_AMOUNT, JETTON_DECIMALS),
        recipient_address=router_address,
        forward_amount=to_nano(0.205),
        user_wallet_address=wallet.address,
        min_amount=1,
        ask_jetton_wallet_address=ask_jetton_wallet_address,
    )

    tx_hash = await wallet.transfer(
        destination=offer_address,
        amount=0.205 + 0.265,
        body=body,
    )

    print("Successfully swapped Jetton to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
