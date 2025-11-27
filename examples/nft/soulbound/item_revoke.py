from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import NFTRevokeBody, WalletV4R2
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."

NFT_ITEM_ADDRESS = Address("EQ...")


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = NFTRevokeBody()

    msg = await wallet.transfer(
        destination=NFT_ITEM_ADDRESS,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    print(f"NFT item address: {NFT_ITEM_ADDRESS.to_str()}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
