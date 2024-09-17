from typing import Any, Dict, List, Optional

from ._base import Client


class TonapiClient(Client):
    """
    TonapiClient class for interacting with the TON blockchain.

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

        :param api_key: The API key for accessing the Tonapi service.
            You can get API key here: https://tonconsole.com.
        :param is_testnet: Flag to indicate if testnet configuration should be used. Defaults to False.
        """
        base_url = "https://tonapi.io/" if not is_testnet else "https://testnet.tonapi.io/"
        headers = {"Authorization": f"Bearer {api_key}"}

        super().__init__(base_url=base_url, headers=headers)

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        method = f"v2/blockchain/accounts/{address}/methods/{method_name}"

        if stack:
            query_params = '&'.join(f"args={arg}" for arg in stack)
            method = f"{method}?{query_params}"

        return await self._get(method=method)

    async def send_message(self, boc: str) -> None:
        method = "v2/blockchain/message"

        await self._post(method=method, body={"boc": boc})

    async def _get_account_info(self, address: str) -> Dict[str, Any]:
        method = f"v2/accounts/{address}"

        return await self._get(method=method)

    async def get_account_balance(self, address: str) -> int:
        account_info = await self._get_account_info(address)

        return int(account_info["balance"])
