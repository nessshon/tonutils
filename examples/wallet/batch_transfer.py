from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    TONTransferBuilder,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)
    # You can also use `NFTTransferBuilder` and `JettonTransferBuilder`
    msg = await wallet.batch_transfer_message(
        [
            TONTransferBuilder(
                destination=Address("UQ..."),
                amount=to_nano(0.01),
                body="Hello from tonutils!",
            ),
            TONTransferBuilder(
                destination=Address("UQ..."),
                amount=to_nano(0.01),
                body="Hello from tonutils!",
            ),
            TONTransferBuilder(
                destination=Address("UQ..."),
                amount=to_nano(0.01),
                body="Hello from tonutils!",
            ),
        ]
    )

    print(f"Wallet address: {wallet.address.to_str(is_bounceable=False)}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
