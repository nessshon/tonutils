from tonutils.clients import LiteClient, LiteBalancer
from tonutils.types import NetworkGlobalID, DEFAULT_ADNL_RETRY_POLICY


async def main() -> None:
    # Common parameters for all LiteBalancer initializers:
    # network:               NetworkGlobalID.MAINNET (-239) for production
    #                        NetworkGlobalID.TESTNET (-3) for testing
    # rps_limit:             requests per second limit
    #                        Avoid rps_limit=1 — parallel background queries are used
    #                        to track masterchain updates
    # rps_per_client:        False → one shared limiter for all clients (default)
    #                        True  → separate limiter per client
    # connect_timeout:       timeout in seconds for a single connect/reconnect attempt
    # request_timeout:       maximum total time in seconds for one balancer operation,
    #                        including all failover attempts across lite-servers
    # retry_policy:          DEFAULT_ADNL_RETRY_POLICY is recommended for stability

    # Direct initialization with explicit lite-server parameters
    # Use when you have specific server credentials from a private provider
    # Recommended providers: dTON (https://t.me/dtontech_bot), Tonconsole (https://tonconsole.com/)
    # ip:         signed 32-bit integer or IPv4 string of the lite-server
    # port:       lite-server port number
    # public_key: server's public key (hex, base64, or bytes)
    client_a = LiteClient(
        network=NetworkGlobalID.MAINNET,
        ip=-1234567890,
        port=12345,
        public_key="Abc123...",
        rps_limit=50,
        retry_policy=DEFAULT_ADNL_RETRY_POLICY,
    )
    client_b = LiteClient(
        network=NetworkGlobalID.MAINNET,
        ip=-987654321,
        port=54321,
        public_key="Zyx987...",
        rps_limit=50,
        retry_policy=DEFAULT_ADNL_RETRY_POLICY,
    )

    # Balancer selects the best client based on masterchain height and ping RTT
    # Falls back to round-robin if all clients are equally available
    balancer = LiteBalancer(
        network=NetworkGlobalID.MAINNET,
        clients=[client_a, client_b],
        connect_timeout=2,
        request_timeout=12,
    )
    async with balancer:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await balancer.get_contract_info(address)
        pass

    # Initialize from a private GlobalConfig (recommended for production)
    # Automatically creates a LiteClient for each server in the config
    # config: full lite-server config dict obtained from your provider
    private_balancer = LiteBalancer.from_config(
        network=NetworkGlobalID.MAINNET,
        config={},
        rps_limit=100,
        retry_policy=DEFAULT_ADNL_RETRY_POLICY,
    )
    async with private_balancer:
        pass

    # Initialize from public TON network config (free, no credentials needed)
    # Fetches lite-server list automatically from TON global config
    # Note: public servers may be unstable under heavy load — use private for production
    public_balancer = LiteBalancer.from_network_config(
        network=NetworkGlobalID.MAINNET,
        rps_limit=50,
        connect_timeout=1,
        request_timeout=10,
        retry_policy=DEFAULT_ADNL_RETRY_POLICY,
    )
    async with public_balancer:
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
