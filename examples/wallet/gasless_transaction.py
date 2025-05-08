"""
Install pytonapi before running:
pip install pytonapi
"""
from pytonapi import AsyncTonapi
from pytoniq_core import Address, Cell

from tonutils.client import TonapiClient
from tonutils.jetton import JettonMasterStandard, JettonWalletStandard
from tonutils.utils import to_nano
from tonutils.wallet import WalletV5R1

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of Jettons to transfer (in base units, considering decimals)
JETTON_AMOUNT = 0.01

# The address of the recipient
DESTINATION_ADDRESS = "UQ..."

# Amount for jetton transfer.
BASE_JETTON_SEND_AMOUNT = 0.05


async def main() -> None:
    tonapi, client = AsyncTonapi(api_key=API_KEY), TonapiClient(api_key=API_KEY)
    wallet, public_key, private_key, _ = WalletV5R1.from_mnemonic(client, MNEMONIC)

    gasless_config = await tonapi.gasless.get_config()
    relayer_address = Address(gasless_config.relay_address)

    jetton_wallet_address = await JettonMasterStandard.get_wallet_address(
        client=client,
        owner_address=wallet.address,
        jetton_master_address=JETTON_MASTER_ADDRESS,
    )
    tether_transfer_body = JettonWalletStandard.build_transfer_body(
        jetton_amount=to_nano(JETTON_AMOUNT, JETTON_DECIMALS),
        recipient_address=Address(DESTINATION_ADDRESS),
        response_address=relayer_address,
        forward_amount=1,
    )
    message_to_estimate = wallet.create_internal_msg(
        dest=jetton_wallet_address,
        value=to_nano(BASE_JETTON_SEND_AMOUNT),
        body=tether_transfer_body,
    )

    sign_raw_params = await tonapi.gasless.estimate_gas_price(
        master_id=JETTON_MASTER_ADDRESS,
        body={
            "wallet_address": wallet.address.to_str(),
            "wallet_public_key": public_key.hex(),
            "messages": [
                {
                    "boc": message_to_estimate.serialize().to_boc().hex(),
                }
            ]
        }
    )

    try:
        seqno = await WalletV5R1.get_seqno(client, wallet.address)
    except (Exception,):
        seqno = 0

    tether_transfer_for_send = wallet.create_signed_internal_msg(
        messages=[
            wallet.create_wallet_internal_message(
                destination=Address(message.address),
                value=int(message.amount),
                body=Cell.one_from_boc(message.payload),
            ) for message in sign_raw_params.messages
        ],
        seqno=seqno,
        valid_until=sign_raw_params.valid_until,
    )
    ext_message = wallet.create_external_msg(
        dest=wallet.address,
        body=tether_transfer_for_send,
        state_init=wallet.state_init if seqno == 0 else None,
    )

    await tonapi.gasless.send(
        body={
            "wallet_public_key": public_key.hex(),
            "boc": ext_message.serialize().to_boc().hex(),
        }
    )

    print(f"A gasless transfer sent!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
