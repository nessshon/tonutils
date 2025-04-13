import base64
import json
from typing import Any, Dict, List, Optional

import aiohttp
from pytoniq_core import Cell

from ._base import Client
from .utils import RunGetMethodStack, RunGetMethodResult
from ..account import AccountStatus, RawAccount
from ..utils import boc_to_base64_string


class QuicknodeClient(Client):
    """
    QuicknodeClient class for interacting with the TON blockchain.

    This class provides methods to run get methods and send messages to the blockchain,
    with options for network selection.
    """

    def __init__(
            self,
            http_provider_url: str
    ) -> None:
        """
        Initialize the QuicknodeClient.

        :param http_provider_url: The HTTP provider URL for the Quicknode service.
            You can get URL here: https://quicknode.com
        """
        if http_provider_url.endswith("/"):
            http_provider_url = http_provider_url[:-1]
        super().__init__(base_url=http_provider_url)

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
