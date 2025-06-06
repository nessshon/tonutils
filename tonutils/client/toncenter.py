import base64
from typing import Any, Dict, List, Optional

from pytoniq_core import Builder, Cell, HashMap

from ._base import Client
from .utils import RunGetMethodStack, RunGetMethodResult, unpack_config
from ..account import AccountStatus, RawAccount
from ..utils import boc_to_base64_string


class ToncenterV2Client(Client):
    """
    ToncenterV2Client class for interacting with the TON blockchain.

    Provides methods to query and send messages to the blockchain,
    with support for both mainnet and testnet environments.
    """

    API_VERSION_PATH = "/api/v2"

    def __init__(
            self,
            api_key: Optional[str] = None,
            is_testnet: bool = False,
            base_url: Optional[str] = None,
            rps: Optional[int] = None,
            max_retries: int = 1,
    ) -> None:
        """
        Initialize the ToncenterV2Client.

        :param api_key: The API key for accessing the Toncenter service.
            Obtain one at: https://t.me/tonapibot
        :param is_testnet: Whether to use the testnet environment. Defaults to False.
        :param base_url: Optional custom base URL for the Toncenter API.
            If not set, defaults to the official Toncenter URLs.
        :param rps: Optional requests per second (RPS) limit.
        :param max_retries: Number of retries for rate-limited requests. Defaults to 1.
        """
        default_url = "https://testnet.toncenter.com" if is_testnet else "https://toncenter.com"
        base_url = (base_url or default_url).rstrip("/") + self.API_VERSION_PATH
        headers = {"X-Api-Key": api_key} if api_key else {}

        super().__init__(
            base_url=base_url,
            headers=headers,
            is_testnet=is_testnet,
            rps=rps,
            max_retries=max_retries,
        )

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        stack = RunGetMethodStack(self, stack).pack_to_toncenter()
        method = f"/runGetMethod"

        body = {
            "address": address,
            "method": method_name,
            "stack": [
                ["num", str(v)]
                if isinstance(v, int) else
                ["slice", v]
                for v in (stack or [])
            ],
        }

        result = await self._post(method=method, body=body)
        return RunGetMethodResult(self, result["stack"]).parse_from_toncenter()

    async def send_message(self, boc: str) -> None:
        method = "/sendBoc"

        await self._post(method=method, body={"boc": boc_to_base64_string(boc)})

    async def get_raw_account(self, address: str) -> RawAccount:
        method = f"/getAddressInformation"
        params = {"address": address}
        result = await self._get(method=method, params=params)

        status = (
            "uninit"
            if result.get("state") == "uninitialized" or result.get("state") is None else
            result.get("state")
        )
        code = result.get("code")
        code_cell = Cell.one_from_boc(code) if code else None
        data = result.get("data")
        data_cell = Cell.one_from_boc(data) if data else None

        last_transaction_id = result.get("last_transaction_id", {})
        _lt, _lt_hash = last_transaction_id.get("lt"), last_transaction_id.get("hash")
        lt, lt_hash = int(_lt) if _lt else None, base64.b64decode(_lt_hash).hex() if _lt_hash else None

        return RawAccount(
            balance=int(result.get("balance", 0)),
            code=code_cell,
            data=data_cell,
            status=AccountStatus(status),
            last_transaction_lt=lt,
            last_transaction_hash=lt_hash,
        )

    async def get_account_balance(self, address: str) -> int:
        raw_account = await self.get_raw_account(address)

        return raw_account.balance

    async def get_config_params(self) -> Dict[int, Any]:
        method = "/getConfigAll"
        result = await self._get(method=method)

        config = result.get("config")
        if not config or "bytes" not in config:
            raise ValueError("Invalid config response: missing 'bytes' field")
        dict_cell = Cell.one_from_boc(config["bytes"])

        config_map = HashMap.parse(
            dict_cell=dict_cell.begin_parse(),
            key_length=32,
            key_deserializer=lambda src: Builder().store_bits(src).to_slice().load_int(32),
            value_deserializer=lambda src: src.load_ref().begin_parse(),
        )
        return unpack_config(config_map)


class ToncenterV3Client(Client):
    """
    ToncenterV3Client for interacting with the TON blockchain via Toncenter API v3.

    This client allows querying and sending messages to the blockchain,
    with support for mainnet and testnet environments.
    """

    API_VERSION_PATH = "/api/v3"

    def __init__(
            self,
            api_key: Optional[str] = None,
            is_testnet: bool = False,
            base_url: Optional[str] = None,
            rps: Optional[int] = None,
            max_retries: int = 1,
    ) -> None:
        """
        Initialize the ToncenterV3Client.

        :param api_key: Optional API key for accessing Toncenter services.
            You can get an API key at: https://t.me/tonapibot
        :param is_testnet: Use testnet if True; defaults to mainnet.
        :param base_url: Optional custom base URL for Toncenter API.
            Defaults to official Toncenter endpoints.
        :param rps: Optional requests per second (RPS) limit.
        :param max_retries: Number of retries for rate-limited requests. Defaults to 1.
        """
        default_url = (
            "https://testnet.toncenter.com"
            if is_testnet else
            "https://toncenter.com"
        )
        base_url = (base_url or default_url).rstrip("/") + self.API_VERSION_PATH
        headers = {"X-Api-Key": api_key} if api_key else {}

        super().__init__(
            base_url=base_url,
            headers=headers,
            is_testnet=is_testnet,
            rps=rps,
            max_retries=max_retries,
        )

    async def run_get_method(
            self,
            address: str,
            method_name: str,
            stack: Optional[List[Any]] = None,
    ) -> Any:
        stack = RunGetMethodStack(self, stack).pack_to_toncenter()
        method = f"/runGetMethod"

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

        result = await self._post(method=method, body=body)
        return RunGetMethodResult(self, result["stack"]).parse_from_toncenter()

    async def send_message(self, boc: str) -> None:
        method = "/message"

        await self._post(method=method, body={"boc": boc_to_base64_string(boc)})

    async def get_raw_account(self, address: str) -> RawAccount:
        method = f"/account"
        params = {"address": address}
        result = await self._get(method=method, params=params)

        code = result.get("code")
        code_cell = Cell.one_from_boc(code) if code else None
        data = result.get("data")
        data_cell = Cell.one_from_boc(data) if data else None
        _lt, _lt_hash = result.get("last_transaction_lt"), result.get("last_transaction_hash")
        lt, lt_hash = int(_lt) if _lt else None, base64.b64decode(_lt_hash).hex() if _lt_hash else None

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

    async def get_config_params(self) -> Dict[int, Any]:
        client = ToncenterV2Client(
            is_testnet=self.is_testnet,
            rps=self.rps,
            max_retries=self.max_retries,
        )
        client.headers = self.headers
        client._limiter = self._limiter

        return await client.get_config_params()
