from tonutils.clients import ToncenterHttpClient
from tonutils.types import NetworkGlobalID, DNSCategory

# Domain name to resolve (TON DNS format)
# Supports .ton domains, .t.me domains, and subdomains (e.g., "example.ton", "username.t.me")
DOMAIN = "ness.ton"


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Resolve DNS record for specified domain and category
    # domain: domain name to query (e.g., "example.ton", "username.t.me")
    # category: DNS record type to retrieve (WALLET, SITE, STORAGE, DNS_NEXT_RESOLVER)
    # Returns DNS record object with category-specific value
    wallet_record = await client.dnsresolve(
        domain=DOMAIN,
        category=DNSCategory.WALLET,
    )

    # Display resolved wallet address
    # is_bounceable=False: standard for wallet contracts (UQ...)
    print(f"Linked wallet: {wallet_record.value.to_str(is_bounceable=False)}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
