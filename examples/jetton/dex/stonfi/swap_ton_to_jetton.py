from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.jetton.dex.stonfi import StonfiRouterV2, StonfiRouterV1
from tonutils.jetton.dex.stonfi.utils import get_stonfi_router_details
from tonutils.utils import to_nano, to_amount
from tonutils.wallet import WalletV4R2

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the Jetton Master for swapping (TON > USD₮)
TO_JETTON_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"  # noqa

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of TON to swap (in base units, considering decimals)
TON_AMOUNT = 1

# Minimum amount of Jettons to receive (in base units, considering decimals)
MIN_AMOUNT = 0


async def main() -> None:
    client = ToncenterV3Client()
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    version, router_address, pton_address = await get_stonfi_router_details(
        offer_address="ton",
        ask_address=TO_JETTON_MASTER_ADDRESS,
        amount=TON_AMOUNT,
        decimals=9,
        is_testnet=client.is_testnet,
    )

    if version == 1:
        router_v1 = StonfiRouterV1(client, router_address, pton_address)

        to, value, body = await router_v1.get_swap_ton_to_jetton_tx_params(
            user_wallet_address=wallet.address,
            ask_jetton_address=Address(TO_JETTON_MASTER_ADDRESS),
            offer_amount=to_nano(TON_AMOUNT),
            min_ask_amount=to_nano(MIN_AMOUNT, JETTON_DECIMALS),
        )
    else:
        router_v2 = StonfiRouterV2(client, router_address, pton_address)

        to, value, body = await router_v2.get_swap_ton_to_jetton_tx_params(
            user_wallet_address=wallet.address,
            receiver_address=wallet.address,
            ask_jetton_address=Address(TO_JETTON_MASTER_ADDRESS),
            offer_amount=to_nano(TON_AMOUNT),
            min_ask_amount=to_nano(MIN_AMOUNT, JETTON_DECIMALS),
            refund_address=wallet.address,
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
