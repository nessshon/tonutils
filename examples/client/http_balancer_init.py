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
    # Common parameters for all HTTP clients:
    # network:      NetworkGlobalID.MAINNET (-239) for production
    #               NetworkGlobalID.TESTNET (-3) for testing
    # rps_limit:    requests per second limit (match your API key tier)
    # retry_policy: DEFAULT_HTTP_RETRY_POLICY is recommended for stability

    # Toncenter: Official TON Center API (v2)
    # API key optional — obtain via https://t.me/toncenter
    #   Without key: 1 rps | Free key: 10 rps | Paid: higher RPS
    toncenter = ToncenterClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=1,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # Tonapi: TonAPI by Tonkeeper
    # API key required — obtain via https://tonconsole.com/
    tonapi = TonapiClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=10,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # Chainstack: Enterprise blockchain infrastructure
    # Personal endpoint URL required — obtain via https://chainstack.com/
    chainstack = ChainstackClient(
        network=NetworkGlobalID.MAINNET,
        http_provider_url="https://your-endpoint",
        rps_limit=50,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # QuickNode: High-performance RPC
    # Mainnet only — testnet is not supported
    # Personal endpoint URL required — obtain via https://www.quicknode.com/
    quicknode = QuicknodeClient(
        http_provider_url="https://your-endpoint",
        rps_limit=50,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # Tatum: Multi-chain API platform
    # API key required — obtain via https://tatum.io/
    tatum = TatumClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=20,
        retry_policy=DEFAULT_HTTP_RETRY_POLICY,
    )

    # HTTP Balancer — distributes requests across multiple providers
    # Selects the best available client based on limiter readiness and error rates
    # Falls back to round-robin if all clients are equally available
    # network:         used to validate that all clients share the same network
    # clients:         list of HTTP clients to balance across
    # request_timeout: maximum total time in seconds for one balancer operation,
    #                  including all failover attempts across providers
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
