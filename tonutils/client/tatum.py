from typing import Optional

from .toncenter import ToncenterV2Client


class TatumClient(ToncenterV2Client):
    """
    TatumClient for interacting with the TON blockchain via Tatum's gateway.

    Inherits from ToncenterV2Client and configures the appropriate base URL
    and headers for use with the Tatum API.
    """

    API_VERSION_PATH = ""  # Tatum uses the root, no versioned path

    def __init__(
            self,
            api_key: str,
            is_testnet: bool = False,
            base_url: Optional[str] = None,
            rps: Optional[int] = None,
            max_retries: int = 1,
    ) -> None:
        """
        Initialize the TatumClient.

        :param api_key: The API key for accessing the Tatum gateway.
            You can obtain one at: https://tatum.io/
        :param is_testnet: Whether to use the testnet environment. Defaults to False.
        :param base_url: Optional custom base URL. Defaults to Tatum's public gateway.
        :param rps: Optional requests per second (RPS) limit.
        :param max_retries: Number of retries for rate-limited requests. Defaults to 1.
        """
        if not api_key:
            raise ValueError("`api_key` is required to initialize TatumClient.")

        default_url = (
            "https://ton-testnet.gateway.tatum.io"
            if is_testnet else
            "https://ton-mainnet.gateway.tatum.io"
        )
        base_url = (base_url or default_url).rstrip("/") + self.API_VERSION_PATH

        super().__init__(
            base_url=base_url,
            api_key=api_key,
            is_testnet=is_testnet,
            rps=rps,
            max_retries=max_retries,
        )
