from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.jetton.dex.dedust import Factory
from tonutils.utils import to_nano, to_amount
from tonutils.wallet import WalletV4R2

# Set to True for the test network, False for the main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "kQC-lmDXBZ5xENZ9zKukBOpCmz81_m8aoPOcrQgVAGDown7O"  # noqa

# Amount of TON to swap
SWAP_TON_AMOUNT = 1


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    to, value, body = await Factory(client).get_swap_ton_to_jetton_tx_params(
        recipient_address=wallet.address,
        offer_jetton_address=Address(JETTON_MASTER_ADDRESS),
        offer_amount=to_nano(SWAP_TON_AMOUNT),
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
