from typing import Any, Optional, List


class Client:
    """
    Base client class for interacting with the TON blockchain.
    """

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        """
        Run a get method on a specified address in the blockchain.

        :param address: The address of the smart contract on the blockchain.
        :param method_name: The name of the method to run on the smart contract.
        :param stack: The stack of arguments to pass to the method. Defaults to None.
        :return: The result of the get method call.
        """
        raise NotImplementedError

    async def send_message(self, boc: str) -> None:
        """
        Send a message to the blockchain.

        :param boc: The bag of cells (BoC) string representation of the message to be sent.
        """
        raise NotImplementedError
