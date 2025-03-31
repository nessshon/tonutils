from typing import Any, List, Optional

from pytoniq_core import Cell

from ._base import Client
from ..account import AccountStatus, RawAccount


class QuickNodeClient(Client):
    def __init__(
            self,
            api_key: str,
            is_testnet: Optional[bool] = False,
            base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize the QuickNodeClient.
        Ref: https://www.quicknode.com/docs/ton
        """
        if base_url is None:
            raise ValueError("You must provide a base URL for the QuickNode service.")
        headers = {"Authorization": f"Bearer {api_key}"}

        super().__init__(base_url=base_url, headers=headers, is_testnet=is_testnet)

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        method = f"/{method_name}?address={address}"
        if stack:
            query_params = '&'.join(f"{key}={value}" for key, value in zip(stack[::2], stack[1::2]))
            method = f"{method}?{query_params}"
        return await self._get(method=method)


    async def send_message(self, boc: str) -> None:
        method = "/sendBocReturnHash"

        await self._post(method=method, body={"boc": boc})


    async def get_raw_account(self, address: str) -> RawAccount:
        method = f"/getAddressInformation?address={address}"
        resp = await self._get(method=method)
        if not resp.get("ok"):
            raise Exception("Failed to get account information for address %s", address)
        result = resp.get("result")
        code = result.get("code")
        code_cell = Cell.one_from_boc(code) if code else None
        data = result.get("data")
        data_cell = Cell.one_from_boc(data) if data else None
        last_transaction = result.get("last_transaction_id")
        _lt, _lt_hash = last_transaction.get("last_transaction_lt"), last_transaction.get("hash")
        lt, lt_hash = int(_lt) if _lt else None, _lt_hash if _lt_hash else None

        return RawAccount(
            balance=int(result.get("balance", 0)),
            code=code_cell,
            data=data_cell,
            status=AccountStatus(result.get("state", "uninit")),
            last_transaction_lt=lt,
            last_transaction_hash=lt_hash,
        )

    async def get_account_balance(self, address: str) -> int:
        raw_account = await self.get_raw_account(address)

        return raw_account.balance