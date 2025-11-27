import typing as t

from aiohttp import ClientSession

from tonutils.clients.http.toncenter.provider import ToncenterHttpProvider
from tonutils.types import NetworkGlobalID


class ChainstackHttpProvider(ToncenterHttpProvider):
    version = ""

    def __init__(
        self,
        network: NetworkGlobalID,
        http_provider_url: str,
        timeout: int = 10,
        session: t.Optional[ClientSession] = None,
        rps_limit: t.Optional[int] = None,
        rps_period: t.Optional[float] = None,
        rps_retries: t.Optional[int] = None,
    ) -> None:
        super().__init__(
            network=network,
            base_url=http_provider_url,
            timeout=timeout,
            session=session,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
        )
