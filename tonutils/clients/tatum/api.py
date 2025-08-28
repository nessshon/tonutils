import typing as t

from ..toncenter.api import ToncenterAPI


class TatumAPI(ToncenterAPI):

    def __init__(
        self,
        api_key: str,
        is_testnet: bool = False,
        base_url: t.Optional[str] = None,
        rps: t.Optional[int] = None,
        max_retries: t.Optional[int] = None,
    ) -> None:
        mainnet_url = "https://ton-mainnet.gateway.tatum.io"
        testnet_url = "https://ton-testnet.gateway.tatum.io"
        default_url = testnet_url if is_testnet else mainnet_url

        base_url = base_url or default_url

        super().__init__(
            api_key=api_key,
            is_testnet=is_testnet,
            base_url=base_url,
            rps=rps,
            max_retries=max_retries,
        )
