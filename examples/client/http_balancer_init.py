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

Common parameters:
- network:
    NetworkGlobalID.MAINNET (-239) for production
    NetworkGlobalID.TESTNET (-3) for testing
    note: QuickNode does not accept `network` (mainnet only)
- request_timeout: Maximum total time in seconds for a balancer operation,
    including all failover attempts across providers
- timeout: Total request timeout in seconds per client.
- session: Optional external aiohttp session.
- headers: Default headers for owned session.
- cookies: Default cookies for owned session.
- rps_limit: Optional requests-per-period limit.
- rps_period: Rate limit period in seconds.
- retry_policy: Optional retry policy that defines per-error-code retry rules
"""

from tonutils.clients import (
    ToncenterClient,
    TonapiClient,
    ChainstackClient,
    QuicknodeClient,
    TatumClient,
    HttpBalancer,
)
from tonutils.types import NetworkGlobalID, DEFAULT_HTTP_RETRY_POLICY


async def main() -> None:
    # Toncenter HTTP Client
    # API key optional, obtain via: https://t.me/toncenter
    #   1 rps without API key
    #   10 rps with free API key
    #   paid plans offer higher RPS
    toncenter = ToncenterClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=1,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # Tonapi HTTP Client
    # API key required, obtain via: https://tonconsole.com/
    tonapi = TonapiClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=10,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # Chainstack HTTP Client
    # Personal endpoint required, obtain via: https://chainstack.com/
    chainstack = ChainstackClient(
        network=NetworkGlobalID.MAINNET,
        http_provider_url="https://your-endpoint",
        rps_limit=50,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # QuickNode HTTP Client
    # Mainnet only (testnet not supported)
    # Personal endpoint required, obtain via: https://www.quicknode.com/
    quicknode = QuicknodeClient(
        http_provider_url="https://your-endpoint",
        rps_limit=50,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # Tatum HTTP Client
    # API key required, obtain via: https://tatum.io/
    tatum = TatumClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=20,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # HTTP Balancer
    # Distributes requests across multiple providers automatically
    # Selects best available client based on limiter readiness and error rates
    balancer = HttpBalancer(
        network=NetworkGlobalID.MAINNET,
        request_timeout=12.0,
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
