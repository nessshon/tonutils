import aiohttp
from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.jetton.dex.stonfi import StonfiRouterV2
from tonutils.utils import to_nano, to_amount
from tonutils.wallet import WalletV4R2

# Set to True for the test network, False for the main network
IS_TESTNET = False

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"  # noqa
TO_JETTON_MASTER_ADDRESS = "EQAvlWFDxGF2lXm67y4yzC17wYKD9A0guwPkMs1gOsM__NOT"  # noqa

# Number of decimal places for the Jetton
FROM_JETTON_DECIMALS = 6
TO_JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Retrieve the correct router address before performing a swap
    # The router address determines the entry point to the DEX for processing swaps
    # and must be fetched dynamically based on the swap parameters.
    router_address = await get_router_address()
    stonfi_router = StonfiRouterV2(client, router_address=Address(router_address))

    to, value, body = await stonfi_router.get_swap_jetton_to_jetton_tx_params(
        user_wallet_address=wallet.address,
        receiver_address=wallet.address,
        refund_address=wallet.address,
        offer_jetton_address=Address(FROM_JETTON_MASTER_ADDRESS),
        ask_jetton_address=Address(TO_JETTON_MASTER_ADDRESS),
        offer_amount=to_nano(JETTON_AMOUNT, FROM_JETTON_DECIMALS),
        min_ask_amount=to_nano(0, TO_JETTON_DECIMALS),
    )

    tx_hash = await wallet.transfer(
        destination=to,
        amount=to_amount(value),
        body=body,
    )

    print("Successfully swapped Jetton to Jetton!")
    print(f"Transaction hash: {tx_hash}")


async def get_router_address() -> str:
    """ Simulate the swap using the STON.fi API to get the correct router address. """
    url = "https://api.ston.fi/v1/swap/simulate"
    headers = {"Accept": "application/json"}

    params = {
        "offer_address": FROM_JETTON_MASTER_ADDRESS,
        "ask_address": TO_JETTON_MASTER_ADDRESS,
        "units": to_nano(JETTON_AMOUNT, FROM_JETTON_DECIMALS),
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
