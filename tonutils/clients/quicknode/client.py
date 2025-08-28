import typing as t

from .api import QuicknodeAPI
from ..toncenter.client import ToncenterClient


class QuicknodeClient(ToncenterClient):

    def __init__(
        self,
        http_provider_url: str,
        rps: t.Optional[int] = None,
        max_retries: int = 2,
    ) -> None:
        super().__init__(is_testnet=False)
        self.api = QuicknodeAPI(
            http_provider_url=http_provider_url,
            rps=rps,
            max_retries=max_retries,
        )
