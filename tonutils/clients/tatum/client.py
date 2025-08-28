import typing as t

from .api import TatumAPI
from ..toncenter.client import ToncenterClient


class TatumClient(ToncenterClient):

    def __init__(
        self,
        api_key: str,
        is_testnet: bool = False,
        base_url: t.Optional[str] = None,
        rps: t.Optional[int] = None,
        max_retries: int = 2,
    ) -> None:
        super().__init__(is_testnet=is_testnet)
        self.api = TatumAPI(
            api_key=api_key,
            is_testnet=is_testnet,
            base_url=base_url,
            rps=rps,
            max_retries=max_retries,
        )
