from typing import Optional, Any, List

from pytonapi import AsyncTonapi

from ._base import Client


class TonapiClient(Client):
    """
    TonapiClient class for interacting with the TON blockchain using AsyncTonapi.

    This class provides methods to run get methods and send messages to the blockchain,
    with options for network selection.
    """

    def __init__(
            self,
            api_key: str,
            is_testnet: Optional[bool] = False,
    ) -> None:
        """
        Initialize the TonapiClient.

        :param api_key: The API key for accessing the Tonapi service. You can get API key here: https://tonconsole.com.
        :param is_testnet: Flag to indicate if testnet configuration should be used. Defaults to False.
        """
        self.client = AsyncTonapi(api_key, is_testnet)

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        return await self.client.blockchain.execute_get_method(
            address,
            method_name,
            *stack or []
        )

    async def send_message(self, boc: str) -> None:
        await self.client.blockchain.send_message({"boc": boc})
