from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    JettonMasterStablecoinData,
    JettonMasterStablecoinV2,
    JettonTopUpBody,
    JettonWalletStablecoinV2,
    OffchainContent,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."

ADMIN_ADDRESS = Address("UQ...")

JETTON_MASTER_URI = "https://example.com/jetton.json"


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    jetton_wallet_code = JettonWalletStablecoinV2.get_default_code()
    jetton_master_content = OffchainContent(uri=JETTON_MASTER_URI)

    jetton_master_data = JettonMasterStablecoinData(
        admin_address=ADMIN_ADDRESS,
        content=jetton_master_content,
        jetton_wallet_code=jetton_wallet_code,
    )
    jetton_master = JettonMasterStablecoinV2.from_data(
        client=client,
        data=jetton_master_data.serialize(),
    )
    body = JettonTopUpBody()

    msg = await wallet.transfer(
        destination=jetton_master.address,
        amount=to_nano(0.05),
        body=body.serialize(),
        state_init=jetton_master.state_init,
    )

    print(f"Jetton master address: {jetton_master.address.to_str()}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
