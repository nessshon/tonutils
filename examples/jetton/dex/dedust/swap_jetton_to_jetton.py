from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.jetton.dex.dedust import Factory
from tonutils.utils import to_nano, to_amount
from tonutils.wallet import WalletV4R2

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQ..."  # noqa
TO_JETTON_MASTER_ADDRESS = "EQ..."  # noqa

# Number of decimal places for the Jetton
FROM_JETTON_DECIMALS = 6
TO_JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Minimum amount of Jettons to receive (in base units, considering decimals)
MIN_AMOUNT = 0


async def main() -> None:
    client = ToncenterV3Client()
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    to, value, body = await Factory(client).get_swap_jetton_to_jetton_tx_params(
        recipient_address=wallet.address,
        offer_jetton_address=Address(FROM_JETTON_MASTER_ADDRESS),
        ask_jetton_address=Address(TO_JETTON_MASTER_ADDRESS),
        offer_amount=to_nano(JETTON_AMOUNT, FROM_JETTON_DECIMALS),
        min_ask_amount=to_nano(MIN_AMOUNT, TO_JETTON_DECIMALS),
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
