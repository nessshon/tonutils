from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    ChangeDNSRecordBody,
    DNSRecordWallet,
    WalletV4R2,
)
from tonutils.types import DNSCategory, NetworkGlobalID
from tonutils.utils import to_nano

MNEMONIC = "word1 word2 word3 ..."

DNS_ITEM_ADDRESS = Address("EQ...")


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # DNS categories and their record and value types:
    #   DNSCategory.DNS_NEXT_RESOLVER → DNSRecordDNSNextResolver (accepts: `Address`)
    #   DNSCategory.STORAGE           → DNSRecordStorage         (accepts: `BagID`)
    #   DNSCategory.WALLET            → DNSRecordWallet          (accepts: `Address`)
    #   DNSCategory.SITE              → DNSRecordSite            (accepts: `ADNL`)
    body = ChangeDNSRecordBody(
        category=DNSCategory.WALLET,
        record=DNSRecordWallet(wallet.address),
    )

    msg = await wallet.transfer(
        destination=DNS_ITEM_ADDRESS,
        amount=to_nano(0.05),
        body=body.serialize(),
    )

    print(f"DNS item address: {DNS_ITEM_ADDRESS.to_str()}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
