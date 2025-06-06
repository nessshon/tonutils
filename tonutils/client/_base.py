from __future__ import annotations

import asyncio
import json
import random
from typing import Any, Optional, List, Dict

import aiohttp
from aiolimiter import AsyncLimiter

from ..account import RawAccount
from ..exceptions import *


class Client:
    """
    Base client class for interacting with the TON blockchain.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.base_url = kwargs.get("base_url", "")
        self.headers = kwargs.get("headers", {})
        self.timeout = kwargs.get("timeout", 10)
        self.is_testnet = kwargs.get("is_testnet", False)

        self.rps = kwargs.get("rps", 1)
        self.max_retries = kwargs.get("max_retries", 0)

        self._limiter = AsyncLimiter(
            max_rate=self.rps,
            time_period=1,
        ) if self.rps else None

    @staticmethod
    async def _parse_response(response: aiohttp.ClientResponse) -> Any:
        """
        Parse and normalize the HTTP response content.

        Handles Toncenter-style responses like {"ok": false, "result": "..."}.

        :param response: aiohttp response object.
        :return: Parsed content (dict or str), or normalized error dict.
        """
        if "application/json" not in response.headers.get("Content-Type", ""):
            return {"error": f"Unsupported response format. HTTP {response.status}"}

        raw_data = await response.read()
        try:
            content = json.loads(raw_data.decode())
        except json.JSONDecodeError:
            content = raw_data.decode()

        if isinstance(content, dict) and "ok" in content:
            if not content.get("ok", False):
                return {
                    "error": content.get("result"),
                    "code": content.get("code", 0)
                }
            return content.get("result")

        return content

    @staticmethod
    async def _apply_retry_delay(
            response: Optional[aiohttp.ClientResponse] = None,
            default_delay: int = 1,
    ) -> None:
        """
        Wait for a retry delay based on the 'Retry-After' header or fallback.

        Adds random jitter to avoid retry bursts.

        :param response: aiohttp response with optional 'Retry-After' header.
        :param default_delay: Default delay in seconds if header not found or invalid.
        """
        retry_after = default_delay

        if response and "Retry-After" in response.headers:
            raw_value = response.headers["Retry-After"]
            try:
                retry_after = int(raw_value)
            except (ValueError, TypeError):
                retry_after = default_delay

        seconds = retry_after + random.uniform(0.2, 0.5)
        await asyncio.sleep(seconds)

    async def _request(
            self,
            method: str,
            path: str,
            params: Optional[Dict[str, Any]] = None,
            body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Perform an HTTP request with retry logic for rate limiting (HTTP 429).

        :param method: HTTP method ("GET", "POST", etc.).
        :param path: Endpoint path to append to base URL.
        :param params: Optional query parameters.
        :param body: Optional request JSON body.

        :return: Parsed response content as a dictionary.

        :raises RateLimitExceeded: if all retries are exhausted due to 429.
        :raises UnauthorizedError: if response status is 401.
        :raises HTTPClientResponseError: for any other non-OK responses.
        """
        url = f"{self.base_url}{path}"

        for attempt in range(self.max_retries + 1):
            if self._limiter:
                await self._limiter.acquire()

            try:
                async with aiohttp.ClientSession(
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as session:
                    async with session.request(
                            method=method,
                            url=url,
                            params=params,
                            json=body,
                    ) as response:
                        content = await self._parse_response(response)

                        if response.status == 429 or (isinstance(content, dict) and content.get("code") == 429):
                            await self._apply_retry_delay(response)
                            continue
                        if response.status == 401:
                            raise UnauthorizedError(url)
                        if not response.ok:
                            raise HTTPClientResponseError(url, response.status, str(content))

                        return content

            except (aiohttp.ClientError, asyncio.TimeoutError):
                raise

        raise RateLimitExceeded(url, self.max_retries + 1)

    async def _get(
            self,
            method: str,
            params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request.

        :param method: The API method.
        :param params: Optional query parameters.
        :return: The response content as a dictionary.
        """
        return await self._request("GET", method, params=params)

    async def _post(
            self,
            method: str,
            params: Optional[Dict[str, Any]] = None,
            body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request.

        :param method: The API method.
        :param body: The request body data.
        :return: The response content as a dictionary.
        """
        return await self._request("POST", method, params=params, body=body)

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

    async def get_raw_account(self, address: str) -> RawAccount:
        """
        Retrieve raw account information from the blockchain.

        :param address: The blockchain account address.
        :return: A dictionary containing the account information.
        """
        raise NotImplementedError

    async def get_account_balance(self, address: str) -> int:
        """
        Retrieve the balance of a blockchain account.

        :param address: The blockchain account address.
        :return: The balance of the account as an integer.
        """
        raise NotImplementedError

    async def get_config_params(self) -> Dict[int, Any]:
        """
        Retrieve configuration parameters from the blockchain.

        :return: A dictionary containing the configuration parameters.
        """
        raise NotImplementedError


class LiteBalancer:
    """
    Placeholder class for LiteBalancer when pytoniq is not available.
    Provides stubs for methods that raise errors when called.
    """
    inited = None

    @staticmethod
    def from_config(config: Dict[str, Any], trust_level: int) -> LiteBalancer:
        raise PytoniqDependencyError()

    @staticmethod
    def from_testnet_config(trust_level: int) -> LiteBalancer:
        raise PytoniqDependencyError()

    @staticmethod
    def from_mainnet_config(trust_level: int) -> LiteBalancer:
        raise PytoniqDependencyError()

    async def __aenter__(self) -> LiteBalancer:
        raise PytoniqDependencyError()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        raise PytoniqDependencyError()

    async def run_get_method(self, address: str, method_name: str, stack: List[Any]) -> Any:
        raise PytoniqDependencyError()

    async def raw_send_message(self, message: bytes) -> None:
        raise PytoniqDependencyError()

    async def start_up(self):
        raise PytoniqDependencyError()

    async def close_all(self):
        raise PytoniqDependencyError()

    async def raw_get_account_state(self, address):
        raise PytoniqDependencyError()

    async def get_config_all(self) -> Dict[int, Any]:
        raise PytoniqDependencyError()
