from typing import Any, Dict, List, Optional

from ._base import Client
from ..utils import boc_to_base64_string


class ToncenterClient(Client):
    """
    ToncenterClient class for interacting with the TON blockchain.

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
        base_url = "https://toncenter.com/api/" if not is_testnet else "https://testnet.toncenter.com/api/"
        headers = {"X-Api-Key": api_key}

        super().__init__(base_url=base_url, headers=headers)

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        method = f"v3/runGetMethod"
        body = {
            "address": address,
            "method": method_name,
            "stack": [
                {"type": "num", "value": str(v)}
                if isinstance(v, int) else
                {"type": "slice", "value": v}
                for v in (stack or [])
            ],
        }

        return await self._post(method=method, body=body)

    async def send_message(self, boc: str) -> None:
        method = "v3/message"

        await self._post(method=method, body={"boc": boc_to_base64_string(boc)})

    async def _get_account_info(self, address: str) -> Dict[str, Any]:
        method = f"v3/account"
        params = {"address": address}

        return await self._get(method=method, params=params)

    async def get_account_balance(self, address: str) -> int:
        account_info = await self._get_account_info(address)

        return int(account_info["balance"])
