from pytoniq_core import Address

from tonutils.clients import ToncenterClient
from tonutils.contracts import (
    TONDNSItem,
    DNSRecordWallet,
    DNSRecordDNSNextResolver,
    DNSRecordStorage,
    DNSRecordSite,
)
from tonutils.types import NetworkGlobalID

# DNS item address to query (e.g., .ton domain NFT)
DNS_ITEM_ADDRESS = Address("EQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Load DNS item contract from blockchain
    # Fetches current state and DNS records from on-chain data
    dns_item = await TONDNSItem.from_address(
        client=client,
        address=DNS_ITEM_ADDRESS,
    )

    # Iterate through all DNS records stored in the domain
    # dns_records: dict mapping category names to record objects
    for category, record in dns_item.dns_records.items():
        # DNSRecordDNSNextResolver: resolver address for subdomain resolution
        if isinstance(record, DNSRecordDNSNextResolver):
            value = record.value.to_str()
        # DNSRecordWallet: wallet address linked to domain (non-bounceable format)
        elif isinstance(record, DNSRecordWallet):
            value = record.value.to_str(is_bounceable=False)
        # DNSRecordStorage: TON Storage BagID (hex format, uppercase)
        elif isinstance(record, DNSRecordStorage):
            value = record.value.as_hex.upper()
        # DNSRecordSite: ADNL address for TON Site (hex format)
        elif isinstance(record, DNSRecordSite):
            value = record.value.as_hex
        else:
            continue

        # Display DNS record category and its value
        print(f"DNS record `{category}`: {value}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
