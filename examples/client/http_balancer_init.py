"""
HTTP Balancer Example

Demonstrates load balancing across multiple TON HTTP providers
with automatic failover based on limiter readiness and round-robin fallback.

Available providers:
- Toncenter: Official TON Center API (v2)
- Tonapi: TonAPI by Tonkeeper
- Chainstack: Enterprise blockchain infrastructure
- QuickNode: High-performance RPC (mainnet only)
- Tatum: Multi-chain API platform

Common parameters (all clients):
- network:
    NetworkGlobalID.MAINNET (-239) for production
    NetworkGlobalID.TESTNET (-3) for testing
    note: QuickNode does not accept `network` (mainnet only)
- timeout: HTTP request timeout in seconds
- session: optional externally managed aiohttp.ClientSession
- rps_limit: requests per second limit
- rps_period: time window for rate limiting
- rps_retries: retry attempts on rate limit errors
"""

from tonutils.clients import (
    ToncenterHttpClient,
    TonapiHttpClient,
    ChainstackHttpClient,
    QuicknodeHttpClient,
    TatumHttpClient,
    HttpBalancer,
)
from tonutils.types import NetworkGlobalID


async def main() -> None:
    # Toncenter HTTP Client
    # API key optional, obtain via: https://t.me/toncenter
    #   1 rps without API key
    #   10 rps with free API key
    #   paid plans offer higher RPS
    toncenter = ToncenterHttpClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=1,
    )

    # Tonapi HTTP Client
    # API key required, obtain via: https://tonconsole.com/
    tonapi = TonapiHttpClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=10,
    )

    # Chainstack HTTP Client
    # Personal endpoint required, obtain via: https://chainstack.com/
    chainstack = ChainstackHttpClient(
        network=NetworkGlobalID.MAINNET,
        http_provider_url="https://your-endpoint",
        rps_limit=50,
    )

    # QuickNode HTTP Client
    # Mainnet only (testnet not supported)
    # Personal endpoint required, obtain via: https://www.quicknode.com/
    quicknode = QuicknodeHttpClient(
        http_provider_url="https://your-endpoint",
        rps_limit=50,
    )

    # Tatum HTTP Client
    # API key required, obtain via: https://tatum.io/
    tatum = TatumHttpClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=20,
    )

    # HTTP Balancer
    # Distributes requests across multiple providers automatically
    # Selects best available client based on limiter readiness and error rates
    balancer = HttpBalancer(
        network=NetworkGlobalID.MAINNET,
        clients=[toncenter, tonapi, chainstack, quicknode, tatum],
    )
    async with balancer:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await balancer.get_contract_info(address)
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
