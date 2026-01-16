"""
TON HTTP Client Examples

Demonstrates initialization of HTTP API clients for TON Blockchain.
Each client connects to a different RPC provider.

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
- timeout: Total request timeout in seconds.
- session: Optional external aiohttp session.
- headers: Default headers for owned session.
- cookies: Default cookies for owned session.
- rps_limit: Optional requests-per-period limit.
- rps_period: Rate limit period in seconds.
- retry_policy: Optional retry policy that defines per-error-code retry rules
"""

from tonutils.clients import (
    ToncenterHttpClient,
    TonapiHttpClient,
    ChainstackHttpClient,
    QuicknodeHttpClient,
    TatumHttpClient,
)
from tonutils.types import NetworkGlobalID


async def main() -> None:
    # Toncenter HTTP Client
    # API key optional, obtain via: https://t.me/toncenter
    #   1 rps without API key
    #   10 rps with free API key
    #   paid plans offer higher RPS
    toncenter_client = ToncenterHttpClient(
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

    # Tonapi HTTP Client
    # API key required, obtain via: https://tonconsole.com/
    tonapi_client = TonapiHttpClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=10,
    )
    async with tonapi_client:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await tonapi_client.get_contract_info(address)
        pass

    # Chainstack HTTP Client
    # Personal endpoint URL required, obtain via: https://chainstack.com/
    chainstack_client = ChainstackHttpClient(
        network=NetworkGlobalID.MAINNET,
        http_provider_url="https://your-endpoint",
        rps_limit=50,
    )
    async with chainstack_client:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await chainstack_client.get_contract_info(address)
        pass

    # QuickNode HTTP Client
    # Mainnet only (testnet not supported)
    # Personal endpoint URL required, obtain via: https://www.quicknode.com/
    quicknode_client = QuicknodeHttpClient(
        http_provider_url="https://your-endpoint",
        rps_limit=50,
    )
    async with quicknode_client:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await quicknode_client.get_contract_info(address)
        pass

    # Tatum HTTP Client
    # API key required, obtain via: https://tatum.io/
    tatum_client = TatumHttpClient(
        network=NetworkGlobalID.MAINNET,
        api_key="<your api key>",
        rps_limit=20,
    )
    async with tatum_client:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await tatum_client.get_contract_info(address)
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
