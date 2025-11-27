from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    JettonInternalTransferBody,
    JettonStandardMintBody,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."

DESTINATION_ADDRESS = Address("UQ...")
JETTON_MASTER_ADDRESS = Address("EQ...")

JETTON_AMOUNT_TO_MINT = to_nano(1)


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = JettonStandardMintBody(
        internal_transfer=JettonInternalTransferBody(
            jetton_amount=JETTON_AMOUNT_TO_MINT,
            response_address=wallet.address,
            forward_amount=1,
        ),
        destination=DESTINATION_ADDRESS,
        forward_amount=to_nano(0.05),
    )
    msg = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        amount=to_nano(0.075),
        body=body.serialize(),
    )

    print(f"Jetton master address: {JETTON_MASTER_ADDRESS.to_str()}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
