from tonutils.clients import ToncenterHttpClient
from tonutils.types import NetworkGlobalID, DNSCategory

DOMAIN = "ness.ton"


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet_record = await client.dnsresolve(
        domain=DOMAIN,
        category=DNSCategory.WALLET,
    )

    print(f"Linked wallet: {wallet_record.value.to_str(is_bounceable=False)}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
