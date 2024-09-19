import base64
from typing import Any, List, Optional

from pytoniq_core import Cell

from ._base import Client
from ..account import AccountStatus, RawAccount
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

    async def get_raw_account(self, address: str) -> RawAccount:
        method = f"v3/account"
        params = {"address": address}
        result = await self._get(method=method, params=params)

        code = Cell.one_from_boc(result["code"])
        data = Cell.one_from_boc(result["data"])

        return RawAccount(
            balance=int(result["balance"]),
            code=code,
            data=data,
            status=AccountStatus(result["status"]),
            last_transaction_lt=int(result["last_transaction_lt"]),
            last_transaction_hash=base64.b64decode(result["last_transaction_hash"]).hex(),
        )

    async def get_account_balance(self, address: str) -> int:
        raw_account = await self.get_raw_account(address)

        return raw_account.balance
