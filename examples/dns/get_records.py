from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    TONDNSItem,
    DNSRecordWallet,
    DNSRecordDNSNextResolver,
    DNSRecordStorage,
    DNSRecordSite,
)
from tonutils.types import NetworkGlobalID

DNS_ITEM_ADDRESS = Address("EQ...")


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    dns_item = await TONDNSItem.from_address(
        client=client,
        address=DNS_ITEM_ADDRESS,
    )
    for category, record in dns_item.dns_records.items():
        if isinstance(record, DNSRecordDNSNextResolver):
            value = record.value.to_str()
        elif isinstance(record, DNSRecordWallet):
            value = record.value.to_str(is_bounceable=False)
        elif isinstance(record, DNSRecordStorage):
            value = record.value.as_hex.upper()
        elif isinstance(record, DNSRecordSite):
            value = record.value.as_hex
        else:
            continue
        print(f"DNS record `{category}`: {value}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
