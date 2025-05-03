import aiohttp
from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.jetton.dex.stonfi import StonfiRouterV2
from tonutils.jetton.dex.stonfi.v2.pton.constants import PTONAddresses
from tonutils.utils import to_nano, to_amount
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for the test network, False for the main network
IS_TESTNET = False

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the Jetton Master for swapping (TON > USD₮)
TO_JETTON_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"  # noqa

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of TON to swap (in base units, considering decimals)
TON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Retrieve the correct router address before performing a swap
    # The router address determines the entry point to the DEX for processing swaps
    # and must be fetched dynamically based on the swap parameters.
    router_address = await get_router_address()
    stonfi_router = StonfiRouterV2(client, router_address=Address(router_address))

    to, value, body = await stonfi_router.get_swap_ton_to_jetton_tx_params(
        user_wallet_address=wallet.address,
        receiver_address=wallet.address,
        ask_jetton_address=Address(TO_JETTON_MASTER_ADDRESS),
        offer_amount=to_nano(TON_AMOUNT),
        min_ask_amount=0,
        refund_address=wallet.address,
    )

    tx_hash = await wallet.transfer(
        destination=to,
        amount=to_amount(value),
        body=body,
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


async def get_router_address() -> str:
    """ Simulate the swap using the STON.fi API to get the correct router address. """
    url = "https://api.ston.fi/v1/swap/simulate"
    headers = {"Accept": "application/json"}

    params = {
        "offer_address": PTONAddresses.TESTNET if IS_TESTNET else PTONAddresses.MAINNET,
        "ask_address": TO_JETTON_MASTER_ADDRESS,
        "units": to_nano(TON_AMOUNT),
        "slippage_tolerance": 1,
        "dex_v2": "true",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, params=params, headers=headers) as response:
            if response.status == 200:
                content = await response.json()
                return content.get("router_address")
            else:
                error_text = await response.text()
                raise Exception(f"Failed to get router address: {response.status}: {error_text}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
