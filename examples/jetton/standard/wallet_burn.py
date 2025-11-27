from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    get_wallet_address_get_method,
    JettonBurnBody,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

IS_TESTNET = True

MNEMONIC = "word1 word2 word3 ..."

JETTON_MASTER_ADDRESS = Address("EQ...")

JETTON_AMOUNT_TO_BURN = to_nano(1)


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    jetton_wallet_address = await get_wallet_address_get_method(
        client=client,
        address=JETTON_MASTER_ADDRESS,
        owner_address=wallet.address,
    )

    body = JettonBurnBody(
        jetton_amount=JETTON_AMOUNT_TO_BURN,
        response_address=wallet.address,
    )

    msg = await wallet.transfer(
        destination=jetton_wallet_address,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    print(f"Jetton wallet address: {jetton_wallet_address.to_str()}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
