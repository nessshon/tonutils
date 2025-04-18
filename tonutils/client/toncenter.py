import base64
import json
from typing import Any, List, Optional, Dict

import aiohttp
from pytoniq_core import Cell

from ._base import Client
from .utils import RunGetMethodStack, RunGetMethodResult
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
    ) -> None:
        """
        Initialize the ToncenterV2Client.

        :param api_key: The API key for accessing the Toncenter service.
            Obtain one at: https://t.me/tonapibot
        :param is_testnet: Whether to use the testnet environment. Defaults to False.
        :param base_url: Optional custom base URL for the Toncenter API.
            If not set, defaults to the official Toncenter URLs.
        """
        default_url = "https://testnet.toncenter.com" if is_testnet else "https://toncenter.com"
        base_url = (base_url or default_url).rstrip("/") + self.API_VERSION_PATH
        headers = {"X-Api-Key": api_key} if api_key else {}

        super().__init__(base_url=base_url, headers=headers, is_testnet=is_testnet)

    @staticmethod
    async def __read_content(response: aiohttp.ClientResponse) -> Any:
        """
        Read the response content.

        :param response: The HTTP response object.
        :return: The response content.
        """
        try:
            data = await response.read()
            try:
                content = json.loads(data.decode())
            except json.JSONDecodeError:
                content = data.decode()
        except aiohttp.ClientPayloadError as e:
            content = {"error": f"Payload error occurred: {e}"}
        except Exception as e:
            raise aiohttp.ClientError(f"Failed to read response content: {e}")
        if not content.get("ok"):
            raise aiohttp.ClientError(content.get("error", content))

        return content.get("result")

    async def _request(
            self,
            method: str,
            path: str,
            headers: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request.

        :param method: The HTTP method (GET or POST).
        :param path: The API path.
        :param headers: Optional headers to include in the request.
        :param params: Optional query parameters.
        :param body: Optional request body data.
        :return: The response content as a dictionary.
        """
        url = self.base_url + path
        self.headers.update(headers or {})
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.request(
                        method=method,
                        url=url,
                        params=params,
                        json=body,
                        timeout=self.timeout,
                ) as response:
                    content = await self.__read_content(response)

                    if not response.ok:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=content.get("error", content)
                        )

                    return content

        except aiohttp.ClientError:
            raise

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
    ) -> None:
        """
        Initialize the ToncenterV3Client.

        :param api_key: Optional API key for accessing Toncenter services.
            You can get an API key at: https://t.me/tonapibot
        :param is_testnet: Use testnet if True; defaults to mainnet.
        :param base_url: Optional custom base URL for Toncenter API.
            Defaults to official Toncenter endpoints.
        """
        default_url = (
            "https://testnet.toncenter.com"
            if is_testnet else
            "https://toncenter.com"
        )
        base_url = (base_url or default_url).rstrip("/") + self.API_VERSION_PATH
        headers = {"X-Api-Key": api_key} if api_key else {}

        super().__init__(base_url=base_url, headers=headers, is_testnet=is_testnet)

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
