import base64
from typing import Optional, Any, List

from pytoncenter import AsyncTonCenterClientV3
from pytoncenter.v3.models import RunGetMethodRequest, ExternalMessage

from ._base import Client


class ToncenterClient(Client):
    """
    ToncenterClient class for interacting with the TON blockchain using AsyncTonCenterClientV3.

    This class provides methods to run get methods and send messages to the blockchain,
    with options for network selection.
    """

    def __init__(
            self,
            api_key: str,
            is_testnet: Optional[bool] = False,
    ) -> None:
        """
        Initialize the ToncenterClient.

        :param api_key: The API key for accessing the Toncenter service.
            You can get API key here: https://t.me/tonapibot
        :param is_testnet: Flag to indicate if testnet configuration should be used. Defaults to False.
        """
        self.client = AsyncTonCenterClientV3(
            network="testnet" if is_testnet else "mainnet",
            api_key=api_key,
        )

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        req = RunGetMethodRequest(
            address=address,
            method=method_name,
            stack=stack or [],
        )

        return await self.client.run_get_method(req)

    async def send_message(self, boc: str) -> None:
        req = ExternalMessage(boc=base64.b64encode(bytes.fromhex(boc)).decode())
        await self.client.send_message(req)
