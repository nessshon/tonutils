from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.jetton.dex.stonfi import StonfiRouterV2, StonfiRouterV1
from tonutils.jetton.dex.stonfi.utils import get_stonfi_router_details
from tonutils.utils import to_nano, to_amount
from tonutils.wallet import WalletV4R2

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQ..."  # noqa

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1

# Minimum amount of TON to receive
MIN_AMOUNT = 0


async def main() -> None:
    client = ToncenterV3Client()
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    version, router_address, pton_address = await get_stonfi_router_details(
        offer_address=FROM_JETTON_MASTER_ADDRESS,
        ask_address="ton",
        amount=JETTON_AMOUNT,
        decimals=JETTON_DECIMALS,
        is_testnet=client.is_testnet,
    )

    if version == 1:
        router_v1 = StonfiRouterV1(client, router_address, pton_address)

        to, value, body = await router_v1.get_swap_jetton_to_ton_tx_params(
            offer_jetton_address=Address(FROM_JETTON_MASTER_ADDRESS),
            user_wallet_address=wallet.address,
            offer_amount=to_nano(JETTON_AMOUNT, JETTON_DECIMALS),
            min_ask_amount=to_nano(MIN_AMOUNT),
        )
    else:
        router_v2 = StonfiRouterV2(client, router_address, pton_address)

        to, value, body = await router_v2.get_swap_jetton_to_ton_tx_params(
            offer_jetton_address=Address(FROM_JETTON_MASTER_ADDRESS),
            receiver_address=wallet.address,
            user_wallet_address=wallet.address,
            offer_amount=to_nano(JETTON_AMOUNT, JETTON_DECIMALS),
            min_ask_amount=to_nano(MIN_AMOUNT),
            refund_address=wallet.address,
        )

    tx_hash = await wallet.transfer(
        destination=to,
        amount=to_amount(value),
        body=body,
    )

    print("Successfully swapped Jetton to TON!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
