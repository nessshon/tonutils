from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    JettonStandardChangeAdminBody,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."

ADMIN_ADDRESS = Address("UQ...")
JETTON_MASTER_ADDRESS = Address("EQ...")


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = JettonStandardChangeAdminBody(admin_address=ADMIN_ADDRESS)

    msg = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    print(f"Jetton master address: {JETTON_MASTER_ADDRESS.to_str()}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
