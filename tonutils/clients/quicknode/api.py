import typing as t

from ..toncenter.api import ToncenterAPI


class QuicknodeAPI(ToncenterAPI):

    def __init__(
        self,
        http_provider_url: str,
        rps: t.Optional[int] = None,
        max_retries: t.Optional[int] = None,
    ) -> None:
        super().__init__(
            is_testnet=False,
            base_url=http_provider_url,
            rps=rps,
            max_retries=max_retries,
        )
