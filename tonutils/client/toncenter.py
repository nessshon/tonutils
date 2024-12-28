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
            base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize the ToncenterClient.

        :param api_key: The API key for accessing the Toncenter service.
            You can get API key here: https://t.me/tonapibot
        :param is_testnet: Flag to indicate if testnet configuration should be used. Defaults to False.
        :param base_url: Optional base URL for the Toncenter API. If not provided,
            the default public URL will be used. You can specify your own API URL if needed.
        """
        if base_url is None:
            base_url = "https://toncenter.com" if not is_testnet else "https://testnet.toncenter.com"
        headers = {"X-Api-Key": api_key}

        super().__init__(base_url=base_url, headers=headers, is_testnet=is_testnet)

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        method = f"/api/v3/runGetMethod"
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
        method = "/api/v3/message"

        await self._post(method=method, body={"boc": base64.b64encode(bytes.fromhex(boc)).decode()})

    async def get_raw_account(self, address: str) -> RawAccount:
        method = f"/api/v3/account"
        params = {"address": address}
        result = await self._get(method=method, params=params)

        code = result.get("code")
        code_cell = Cell.one_from_boc(code) if code else None
        data = result.get("data")
        data_cell = Cell.one_from_boc(data) if data else None

        return RawAccount(
            balance=int(result["balance"]),
            code=code_cell,
            data=data_cell,
            status=AccountStatus(result["status"]),
            last_transaction_lt=int(result["last_transaction_lt"]),
            last_transaction_hash=base64.b64decode(result["last_transaction_hash"]).hex(),
        )

    async def get_account_balance(self, address: str) -> int:
        raw_account = await self.get_raw_account(address)

        return raw_account.balance
