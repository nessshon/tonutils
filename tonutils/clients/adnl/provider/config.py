from pyapiq import AsyncClientAPI, async_endpoint
from pyapiq.types import HTTPMethod

from tonutils.clients.adnl.provider.models import GlobalConfig


class TONClient(AsyncClientAPI):
    base_url = "https://ton.org/"

    @async_endpoint(
        HTTPMethod.GET,
        path="global-config.json",
        return_as=GlobalConfig,
    )
    async def mainnet_global_config(self) -> GlobalConfig: ...  # type: ignore[empty-body]

    @async_endpoint(
        HTTPMethod.GET,
        path="testnet-global-config.json",
        return_as=GlobalConfig,
    )
    async def testnet_global_config(self) -> GlobalConfig: ...  # type: ignore[empty-body]
