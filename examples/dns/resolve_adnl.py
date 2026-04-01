from ton_core import DNSCategory, NetworkGlobalID

from tonutils.clients import ToncenterClient
from tonutils.clients.dht import DhtNetwork
from tonutils.exceptions import DhtValueNotFoundError

# Domain name to resolve ADNL address for (must have a SITE record)
DOMAIN = "foundation.ton"

# Or specify an ADNL address directly (64-char hex string)
# ADNL_ADDRESS = "abcdef0123456789..."


async def main() -> None:
    # Step 1: Resolve ADNL address from TON DNS
    # Initialize HTTP client for TON blockchain interaction
    client = ToncenterClient(
        network=NetworkGlobalID.MAINNET, rps_limit=1, rps_period=1.2
    )
    await client.connect()

    # Resolve SITE DNS record — it contains the ADNL address
    # category: SITE for TON Sites, returns DNSRecordSite with ADNL value
    site_record = await client.dnsresolve(
        domain=DOMAIN,
        category=DNSCategory.SITE,
    )

    await client.close()

    if site_record is None:
        print(f"No SITE record found for {DOMAIN}")
        return

    adnl = site_record.value
    print(f"Domain:       {DOMAIN}")
    print(f"ADNL address: {adnl}")

    # Step 2: Resolve ADNL address to IP addresses via DHT
    # Initialize DHT network client from mainnet global config
    dht = DhtNetwork.from_network_config(NetworkGlobalID.MAINNET)
    await dht.connect()

    print("\nSearching for addresses in DHT...")

    try:
        addr_list, pub_key = await dht.find_addresses(adnl)
    except DhtValueNotFoundError:
        print("ADNL address not found in DHT")
        await dht.close()
        return

    print(f"Public key:   {pub_key.hex()}")
    print(f"Addresses:    {len(addr_list.addrs)} found")

    for addr in addr_list.addrs:
        print(f"  {addr.endpoint}")

    await dht.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
