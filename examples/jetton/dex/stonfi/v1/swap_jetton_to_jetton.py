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

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "kQBi0fzBTtCfwF1xM6tXMydpJlzfVgtgRmCFx3G--9hx97tM"  # noqa
TO_JETTON_MASTER_ADDRESS = "kQCw3IIGAqo0EylOjMcF8VYs09ikS_F_tV1VnWVgRPAsYl4T"  # noqa

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    to, value, body = await StonfiRouterV1(client).get_swap_jetton_to_jetton_tx_params(
        user_wallet_address=wallet.address,
        offer_jetton_address=Address(FROM_JETTON_MASTER_ADDRESS),
        ask_jetton_address=Address(TO_JETTON_MASTER_ADDRESS),
        offer_amount=to_nano(JETTON_AMOUNT, JETTON_DECIMALS),
        min_ask_amount=0,
    )

    tx_hash = await wallet.transfer(
        destination=to,
        amount=to_amount(value),
        body=body,
    )

    print("Successfully swapped Jetton to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
