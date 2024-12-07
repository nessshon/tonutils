from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.jetton.dex.stonfi import StonfiRouterV1
from tonutils.utils import to_nano, to_amount
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for the test network, False for the main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []  # noqa

# Address of the Jetton Master for swapping
TO_JETTON_MASTER_ADDRESS = "kQBi0fzBTtCfwF1xM6tXMydpJlzfVgtgRmCFx3G--9hx97tM"  # noqa

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of TON to swap (in base units, considering decimals)
TON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    to, value, body = await StonfiRouterV1(client).get_swap_ton_to_jetton_tx_params(
        user_wallet_address=wallet.address,
        ask_jetton_address=Address(TO_JETTON_MASTER_ADDRESS),
        offer_amount=to_nano(TON_AMOUNT),
        min_ask_amount=0,
    )

    tx_hash = await wallet.transfer(
        destination=to,
        amount=to_amount(value),
        body=body,
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
