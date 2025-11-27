from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    JettonTransferBuilder,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."

DESTINATION_ADDRESS = Address("UQ...")
JETTON_MASTER_ADDRESS = Address("EQ...")

# For example: 1 USD₮ (6 decimals → 1 * 10^6)
JETTON_AMOUNT_TO_SEND = to_nano(1, decimals=6)


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    msg = await wallet.transfer_message(
        JettonTransferBuilder(
            destination=DESTINATION_ADDRESS,
            jetton_amount=JETTON_AMOUNT_TO_SEND,
            jetton_master_address=JETTON_MASTER_ADDRESS,
            forward_payload="Hello from tonutils!",
        )
    )

    print(f"Wallet address: {wallet.address.to_str(is_bounceable=False)}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
