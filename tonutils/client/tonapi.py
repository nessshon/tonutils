from typing import Any, List, Optional

from pytoniq_core import Cell

from ._base import Client
from .utils import RunGetMethodStack, RunGetMethodResult
from ..account import AccountStatus, RawAccount


class TonapiClient(Client):
    """
    TonapiClient for interacting with the TON blockchain via TonAPI.

    Provides methods for querying data and sending transactions with support
    for both mainnet and testnet environments.
    """

    API_VERSION_PATH = "/v2"

    def __init__(
            self,
            api_key: str,
            is_testnet: bool = False,
            base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize the TonapiClient.

        :param api_key: API key for accessing TonAPI services.
            You can obtain one at: https://tonconsole.com
        :param is_testnet: If True, uses the testnet endpoint. Defaults to False (mainnet).
        :param base_url: Optional custom base URL. If not provided, uses the official endpoint.
        """
        if not api_key:
            raise ValueError("`api_key` is required to initialize TonapiClient.")

        default_url = "https://testnet.tonapi.io" if is_testnet else "https://tonapi.io"
        base_url = (base_url or default_url).rstrip("/") + self.API_VERSION_PATH
        headers = {"Authorization": f"Bearer {api_key}"}

        super().__init__(base_url=base_url, headers=headers, is_testnet=is_testnet)

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> List[Any]:
        stack = RunGetMethodStack(self, stack or []).pack_to_tonapi()
        method = f"/blockchain/accounts/{address}/methods/{method_name}"

        if stack:
            query_params = '&'.join(f"args={arg}" for arg in stack)
            method = f"{method}?{query_params}"

        result = await self._get(method=method)
        return RunGetMethodResult(self, result["stack"]).parse_from_tonapi()

    async def send_message(self, boc: str) -> None:
        method = "/blockchain/message"

        await self._post(method=method, body={"boc": boc})

    async def get_raw_account(self, address: str) -> RawAccount:
        method = f"/blockchain/accounts/{address}"
        result = await self._get(method=method)

        code = result.get("code")
        code_cell = Cell.one_from_boc(code) if code else None
        data = result.get("data")
        data_cell = Cell.one_from_boc(data) if data else None
        _lt, _lt_hash = result.get("last_transaction_lt"), result.get("last_transaction_hash")
        lt, lt_hash = int(_lt) if _lt else None, _lt_hash if _lt_hash else None

        return RawAccount(
            balance=int(result.get("balance", 0)),
            code=code_cell,
            data=data_cell,
            status=AccountStatus(result.get("status", "uninit")),  # noqa
            last_transaction_lt=lt,
            last_transaction_hash=lt_hash,
        )

    async def get_account_balance(self, address: str) -> int:
        raw_account = await self.get_raw_account(address)

        return raw_account.balance
