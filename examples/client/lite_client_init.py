from tonutils.clients import LiteClient
from tonutils.types import NetworkGlobalID, DEFAULT_ADNL_RETRY_POLICY


async def main() -> None:
    # Common parameters for all LiteClient initializers:
    # network:      NetworkGlobalID.MAINNET (-239) for production
    #               NetworkGlobalID.TESTNET (-3) for testing
    # rps_limit:    requests per second limit
    #               Avoid rps_limit=1 — parallel background queries are used
    #               to track masterchain updates
    # retry_policy: DEFAULT_ADNL_RETRY_POLICY is recommended for stability

    # Direct initialization with explicit lite-server parameters
    # Use when you have specific server credentials from a private provider
    # Recommended providers: dTON (https://t.me/dtontech_bot), Tonconsole (https://tonconsole.com/)
    # ip:         signed 32-bit integer or IPv4 string of the lite-server
    # port:       lite-server port number
    # public_key: server's public key (hex, base64, or bytes)
    client = LiteClient(
        network=NetworkGlobalID.MAINNET,
        ip=-1234567890,
        port=12345,
        public_key="ABCdef0123=...",
        rps_limit=100,
        retry_policy=DEFAULT_ADNL_RETRY_POLICY,
    )
    async with client:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await client.get_contract_info(address)
        pass

    # Initialize from a private GlobalConfig (recommended for production)
    # config: full lite-server config dict obtained from your provider
    # index:  lite-server index within config's "liteservers" array
    client_private = LiteClient.from_config(
        network=NetworkGlobalID.MAINNET,
        config={},
        index=0,
        rps_limit=50,
        retry_policy=DEFAULT_ADNL_RETRY_POLICY,
    )
    async with client_private:
        pass

    # Initialize from public TON network config (free, no credentials needed)
    # Fetches lite-server list automatically from TON global config
    # Note: public servers may be unstable under heavy load — use private for production
    # index: lite-server index within config's "liteservers" array
    client_public = LiteClient.from_network_config(
        network=NetworkGlobalID.MAINNET,
        index=0,
        rps_limit=50,
        retry_policy=DEFAULT_ADNL_RETRY_POLICY,
    )
    async with client_public:
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
