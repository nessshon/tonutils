"""
ADNL Balancer Example

Demonstrates load balancing across multiple TON lite-servers via ADNL protocol
with automatic failover based on masterchain height, ping RTT, and round-robin fallback.

Where to obtain lite-server configs:
- Private (recommended):
    dTON bot: https://t.me/dtontech_bot
    Tonconsole: https://tonconsole.com/
- Public (free):
    Can be fetched via `from_network_config()`, but may be unstable under load

Common parameters:
- network:
    NetworkGlobalID.MAINNET (-239) for production
    NetworkGlobalID.TESTNET (-3) for testing
- rps_limit: requests per second limit
- connect_timeout: timeout for connect/reconnect attempts
- rps_limit: shared or per-provider requests per second limit
- rps_period: time window for rate limiting
- rps_per_provider:
    False -> one shared limiter for all providers
    True  -> separate limiter per lite-server

Note: Avoid rps_limit=1, parallel background queries run for masterchain updates.
"""

from tonutils.clients import AdnlClient, AdnlBalancer
from tonutils.types import NetworkGlobalID


async def main() -> None:
    # Direct initialization with lite-server parameters
    # ip: signed 32-bit integer or IPv4 string
    # port: lite-server port
    # public_key: hex, base64, or bytes
    client_a = AdnlClient(
        network=NetworkGlobalID.MAINNET,
        ip=-1234567890,
        port=12345,
        public_key="Abc123...",
        rps_limit=50,
    )
    client_b = AdnlClient(
        network=NetworkGlobalID.MAINNET,
        ip=-987654321,
        port=54321,
        public_key="Zyx987...",
        rps_limit=50,
    )
    balancer = AdnlBalancer(
        network=NetworkGlobalID.MAINNET,
        clients=[client_a, client_b],
        connect_timeout=2,
    )
    async with balancer:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await balancer.get_contract_info(address)
        pass

    # Initialize from private GlobalConfig
    # config: full lite-server config dict from provider
    private_balancer = AdnlBalancer.from_config(
        network=NetworkGlobalID.MAINNET,
        config={},
        rps_limit=100,
    )
    async with private_balancer:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await private_balancer.get_contract_info(address)
        pass

    # Initialize from public TON network config
    # Fetches config automatically from TON global config
    public_balancer = await AdnlBalancer.from_network_config(
        network=NetworkGlobalID.MAINNET,
        rps_limit=50,
        rps_retries=3,
    )
    async with public_balancer:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await public_balancer.get_contract_info(address)
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
