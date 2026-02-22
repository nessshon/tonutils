from tonutils.clients import (
    ToncenterClient,
    TonapiClient,
    ChainstackClient,
    QuicknodeClient,
    TatumClient,
)
from tonutils.types import NetworkGlobalID


async def main() -> None:
    # Common parameters for all HTTP clients:
    # network:      NetworkGlobalID.MAINNET (-239) for production
    #               NetworkGlobalID.TESTNET (-3) for testing
    # rps_limit:    requests per second limit (match your API key tier)
    # rps_period:   time window for rate limiting (default: 1 second)
    # timeout:      total request timeout in seconds
    # retry_policy: optional retry policy per error code

    # Toncenter: Official TON Center API (v2)
    # API key optional — obtain via https://t.me/toncenter
    #   Without key: 1 rps | Free key: 10 rps | Paid: higher RPS
    toncenter_client = ToncenterClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=1,
    )
    async with toncenter_client:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await toncenter_client.get_contract_info(address)
        pass

    # Tonapi: TonAPI by Tonkeeper
    # API key required — obtain via https://tonconsole.com/
    tonapi_client = TonapiClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=10,
    )
    async with tonapi_client:
        pass

    # Chainstack: Enterprise blockchain infrastructure
    # Personal endpoint URL required — obtain via https://chainstack.com/
    # http_provider_url: your personal Chainstack endpoint
    chainstack_client = ChainstackClient(
        network=NetworkGlobalID.MAINNET,
        http_provider_url="https://your-endpoint",
        rps_limit=50,
    )
    async with chainstack_client:
        pass

    # QuickNode: High-performance RPC
    # Mainnet only — testnet is not supported
    # Personal endpoint URL required — obtain via https://www.quicknode.com/
    # http_provider_url: your personal QuickNode endpoint
    quicknode_client = QuicknodeClient(
        http_provider_url="https://your-endpoint",
        rps_limit=50,
    )
    async with quicknode_client:
        pass

    # Tatum: Multi-chain API platform
    # API key required — obtain via https://tatum.io/
    tatum_client = TatumClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=20,
    )
    async with tatum_client:
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
