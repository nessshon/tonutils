from typing import Optional, Any, Dict, List

from pytoniq import LiteBalancer

from ._base import Client


class LiteClient(Client):
    """
    LiteClient class for interacting with the TON blockchain using LiteBalancer.

    This class provides methods to run get methods and send messages to the blockchain,
    with options for configuration and network selection.
    """

    def __init__(
            self,
            config: Optional[Dict[str, Any]] = None,
            is_testnet: Optional[bool] = False,
            trust_level: Optional[int] = 2,
    ) -> None:
        """
        Initialize the LiteClient.

        :param config: The configuration dictionary for LiteBalancer. Defaults to None.
            You can pass your own config from a private lite server,
            which can be acquired from the https://t.me/liteserver_bot.
        :param is_testnet: Flag to indicate if testnet configuration should be used. Defaults to False.
        :param trust_level: The trust level for the LiteBalancer.
            Defines the level of trust for Liteserver communication. Defaults to 2.
            For trustless communication with Liteservers, there are "Proofs" in TON. The trust_level argument
            in the LiteClient constructor defines how much you trust the Liteserver you communicate with.
            Refer to the documentation for more details: https://yungwine.gitbook.io/pytoniq-doc/liteclient/trust-levels
        """
        if config is not None:
            self.client = LiteBalancer.from_config(config=config, trust_level=trust_level)
        elif is_testnet:
            self.client = LiteBalancer.from_testnet_config(trust_level=trust_level)
        else:
            self.client = LiteBalancer.from_mainnet_config(trust_level=trust_level)

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        async with self.client:
            return await self.client.run_get_method(address, method_name, stack or [])

    async def send_message(self, boc: str) -> None:
        async with self.client:
            return await self.client.raw_send_message(bytes.fromhex(boc))
