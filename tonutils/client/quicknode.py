from typing import Optional

from aiohttp import ClientSession

from .toncenter import ToncenterV2Client


class QuicknodeClient(ToncenterV2Client):
    """
    QuicknodeClient for interacting with the TON blockchain via QuickNode.

    Inherits from ToncenterV2Client and uses a custom HTTP provider URL.
    """

    API_VERSION_PATH = ""  # QuickNode does not use versioned path by default

    def __init__(
            self,
            http_provider_url: str,
            rps: Optional[int] = None,
            max_retries: int = 1,
            timeout: Optional[int] = 10,
            session: Optional[ClientSession] = None,
    ) -> None:
        """
        Initialize the QuicknodeClient.

        :param http_provider_url: The full HTTP provider URL for QuickNode.
            You can obtain one at: https://quicknode.com
        :param rps: Optional requests per second (RPS) limit.
        :param max_retries: Number of retries for rate-limited requests. Defaults to 1.
        :param timeout: Response timeout in seconds. Not used if session is specified. Defaults to 10.
        :param session: Aiohttp session to avoid creating new ones every time. By default, a new one is created for each request. If specified, remember to call session_close when finished.
        """
        if not http_provider_url:
            raise ValueError("`http_provider_url` is required to initialize QuicknodeClient")

        base_url = http_provider_url.rstrip("/") + self.API_VERSION_PATH
        super().__init__(
            base_url=base_url,
            rps=rps,
            max_retries=max_retries,
            timeout=timeout,
            session=session,
        )
