"""
ADNL Client Example

Demonstrates direct connection to TON lite-servers via ADNL protocol.
ADNL provides the fastest and most direct access to TON blockchain data.

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
- timeout: request timeout in seconds
- rps_limit: requests per second limit
- rps_period: time window for rate limiting
- rps_retries: retry attempts on rate limit errors

Note: Avoid rps_limit=1, parallel background queries run for masterchain updates.
"""

from tonutils.clients import AdnlClient
from tonutils.types import NetworkGlobalID


async def main() -> None:
    # Direct initialization with lite-server parameters
    # ip: signed 32-bit integer or IPv4 string
    # port: lite-server port
    # public_key: hex, base64, or bytes
    client = AdnlClient(
        network=NetworkGlobalID.MAINNET,
        ip=-1234567890,
        port=12345,
        public_key="ABCdef0123=...",
        rps_limit=100,
    )
    async with client:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await client.get_contract_info(address)
        pass

    # Initialize from private GlobalConfig
    # config: full lite-server config dict from provider
    # index: lite-server index in config's "liteservers" array
    client_private = AdnlClient.from_config(
        network=NetworkGlobalID.MAINNET,
        config={},
        index=0,
        rps_limit=50,
    )
    async with client_private:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await client_private.get_contract_info(address)
        pass

    # Initialize from public TON network config
    # Fetches config automatically from TON global config
    # index: lite-server index in config's "liteservers" array
    client_public = await AdnlClient.from_network_config(
        network=NetworkGlobalID.MAINNET,
        index=0,
        rps_limit=50,
    )
    async with client_public:
        # Example request:
        # from pytoniq_core import Address
        # address = Address("UQ...")
        # info = await client_public.get_contract_info(address)
        pass


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
