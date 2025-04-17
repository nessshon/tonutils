from .toncenter import ToncenterV2Client


class QuicknodeClient(ToncenterV2Client):
    """
    QuicknodeClient for interacting with the TON blockchain via QuickNode.

    Inherits from ToncenterV2Client and uses a custom HTTP provider URL.
    """

    API_VERSION_PATH = ""  # QuickNode does not use versioned path by default

    def __init__(self, http_provider_url: str) -> None:
        """
        Initialize the QuicknodeClient.

        :param http_provider_url: The full HTTP provider URL for QuickNode.
            You can obtain one at: https://quicknode.com
        """
        if not http_provider_url:
            raise ValueError("`http_provider_url` is required to initialize QuicknodeClient")

        base_url = http_provider_url.rstrip("/") + self.API_VERSION_PATH
        super().__init__(base_url=base_url)
