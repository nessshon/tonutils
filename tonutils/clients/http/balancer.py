from __future__ import annotations

import asyncio
import time
import typing as t
from contextlib import suppress
from dataclasses import dataclass
from itertools import cycle

from pyapiq.exceptions import (
    APIQException,
    APIClientResponseError,
    APIClientServerError,
    APIClientTooManyRequestsError,
    RateLimitExceeded,
)
from pytoniq_core import Transaction

from tonutils.clients.base import BaseClient
from tonutils.clients.http.quicknode import QuicknodeHttpClient
from tonutils.exceptions import ClientError, ClientNotConnectedError
from tonutils.types import ClientType, ContractStateInfo, NetworkGlobalID

_T = t.TypeVar("_T")


@dataclass
class HttpClientState:
    """
    Internal state container for an HTTP client.

    Tracks error count and cooldown timeout for retry scheduling.
    """

    client: BaseClient
    retry_after: t.Optional[float] = None
    error_count: int = 0


class HttpBalancer(BaseClient):
    """
    Multi-provider HTTP client with automatic failover and load balancing.

    Selects the best available HTTP client using limiter readiness,
    error counters and round-robin tie-breaking.
    """

    TYPE = ClientType.HTTP

    def __init__(
        self,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        clients: t.List[BaseClient],
    ) -> None:
        """
        Initialize HTTP balancer.

        Each supported HTTP client requires its own credentials or endpoint
        configuration. You can obtain them from the corresponding provider:
            - ToncenterHttpClient:
                API key available via Telegram bot: https://t.me/toncenter
            - TonapiHttpClient:
                API key available on the Tonconsole website: https://tonconsole.com/
            - ChainstackHttpClient:
                Personal endpoint available on: https://chainstack.com/
            - QuicknodeHttpClient:
                Personal endpoint available on: https://www.quicknode.com/
            - TatumHttpClient:
                API key available on: https://tatum.io/

        :param network: Target TON network (mainnet or testnet)
        :param clients: List of HTTP BaseClient instances to balance between
        """
        self.network = network

        self._clients: t.List[BaseClient] = []
        self._states: t.List[HttpClientState] = []
        self.__init_clients(clients)

        self._rr = cycle(self._clients)

        self._retry_after_base = 1.0
        self._retry_after_max = 10.0

    def __init_clients(
        self,
        clients: t.List[BaseClient],
    ) -> None:
        """Validate and register input HTTP clients."""
        for client in clients:
            if client.TYPE != ClientType.HTTP:
                raise ClientError(
                    "HttpBalancer can work only with HTTP clients, "
                    f"got {client.__class__.__name__}."
                )

            if (
                isinstance(client, QuicknodeHttpClient)
                and self.network == NetworkGlobalID.TESTNET
            ):
                raise ClientError(
                    "QuickNode HTTP client does not support testnet network."
                )

            client.network = self.network
            state = HttpClientState(client=client)

            self._clients.append(client)
            self._states.append(state)

    @property
    def clients(self) -> t.Tuple[BaseClient, ...]:
        """
        List of all registered HTTP clients.

        :return: Tuple of BaseClient objects
        """
        return tuple(self._clients)

    @property
    def alive_clients(self) -> t.Tuple[BaseClient, ...]:
        """
        HTTP clients that are allowed to send requests now.

        :return: Tuple of available BaseClient instances
        """
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if state.retry_after is None or state.retry_after <= now
        )

    @property
    def dead_clients(self) -> t.Tuple[BaseClient, ...]:
        """
        HTTP clients currently in cooldown due to previous errors.

        :return: Tuple of unavailable BaseClient instances
        """
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if state.retry_after is not None and state.retry_after > now
        )

    @property
    def provider(self) -> t.Any:
        """
        Provider of the currently selected client.

        :return: Provider instance of chosen HTTP client
        """
        if not self.is_connected:
            raise ClientNotConnectedError(self)
        client = self._pick_client()
        return client.provider

    @property
    def is_connected(self) -> bool:
        """
        Check whether at least one underlying client is connected.

        :return: True if any client is connected, otherwise False
        """
        return any(c.is_connected for c in self._clients)

    async def __aenter__(self) -> HttpBalancer:
        """
        Enter async context manager and connect all underlying clients.

        :return: Self instance with initialized connections
        """
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        """Exit async context manager and close all underlying clients."""
        with suppress(asyncio.CancelledError):
            await self.close()

    def _pick_client(self) -> BaseClient:
        """
        Select the best available HTTP client.

        Selection criteria:
        - minimal limiter waiting time
        - minimal error count
        - round-robin for ties

        :return: Selected BaseClient instance
        """
        alive = list(self.alive_clients)

        height_candidates: t.List[
            t.Tuple[
                float,
                int,
                HttpClientState,
            ]
        ] = []

        for state in self._states:
            client = state.client
            if client not in alive:
                continue

            wait = 0.0
            if client.provider.limiter is not None:
                with suppress(Exception):
                    wait = float(client.provider.limiter.when_ready())
            height_candidates.append((wait, state.error_count, state))

        if not height_candidates:
            raise ClientError("No available HTTP clients in HttpBalancer.")

        height_candidates.sort(key=lambda x: (x[0], x[1]))
        best_wait, best_err, _ = height_candidates[0]

        equal_states: t.List[HttpClientState] = [
            state
            for (w, e, state) in height_candidates
            if w == best_wait and e == best_err
        ]

        if len(equal_states) == 1:
            return equal_states[0].client

        for _ in range(len(self._clients)):
            candidate = next(self._rr)
            for state in equal_states:
                if state.client is candidate:
                    return candidate

        return equal_states[0].client

    def _mark_success(self, client: BaseClient) -> None:
        """
        Reset error state for a successful client.

        Clears cooldown and error counters.
        """
        for state in self._states:
            if state.client is client:
                state.error_count = 0
                state.retry_after = None
                break

    def _mark_error(self, client: BaseClient, *, is_rate_limit: bool) -> None:
        """
        Update error state and schedule retry cooldown.

        Exponential backoff is used with separate handling
        for rate-limit vs generic errors.

        :param client: Client to update
        :param is_rate_limit: Whether the error was rate-limit related
        """
        now = time.monotonic()
        for state in self._states:
            if state.client is client:
                state.error_count += 1
                base = (
                    self._retry_after_base
                    if is_rate_limit
                    else self._retry_after_base / 2
                )
                cooldown = min(
                    base * (2 ** (state.error_count - 1)),
                    self._retry_after_max,
                )
                state.retry_after = now + cooldown
                break

    async def _with_failover(
        self,
        func: t.Callable[[BaseClient], t.Awaitable[_T]],
    ) -> _T:
        """
        Execute a client operation with automatic failover.

        Iterates through available clients until one succeeds
        or all clients fail.

        :param func: Callable performing an operation using a client
        :return: Result of the successful invocation
        """
        last_exc: t.Optional[BaseException] = None

        for _ in range(len(self._clients)):
            if not self.alive_clients:
                break

            client = self._pick_client()

            try:
                result = await func(client)
            except (APIClientTooManyRequestsError, RateLimitExceeded) as e:
                self._mark_error(client, is_rate_limit=True)
                last_exc = e
                continue
            except APIClientResponseError as e:
                last_exc = e
                break
            except (APIClientServerError, APIQException) as e:
                self._mark_error(client, is_rate_limit=False)
                last_exc = e
                continue
            except Exception as e:
                self._mark_error(client, is_rate_limit=False)
                last_exc = e
                continue

            self._mark_success(client)
            return result

        if last_exc is not None:
            raise last_exc

        raise ClientError("All HTTP clients failed to process request.")

    async def _send_boc(self, boc: str) -> None:
        async def _call(client: BaseClient) -> None:
            return await client._send_boc(boc)

        return await self._with_failover(_call)

    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        async def _call(client: BaseClient) -> t.Dict[int, t.Any]:
            return await client._get_blockchain_config()

        return await self._with_failover(_call)

    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        async def _call(client: BaseClient) -> ContractStateInfo:
            return await client._get_contract_info(address)

        return await self._with_failover(_call)

    async def _get_contract_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]:
        async def _call(client: BaseClient) -> t.List[Transaction]:
            return await client._get_contract_transactions(
                address=address,
                limit=limit,
                from_lt=from_lt,
                to_lt=to_lt,
            )

        return await self._with_failover(_call)

    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        async def _call(client: BaseClient) -> t.List[t.Any]:
            return await client._run_get_method(
                address=address,
                method_name=method_name,
                stack=stack,
            )

        return await self._with_failover(_call)

    async def connect(self) -> None:
        await asyncio.gather(
            *(state.client.connect() for state in self._states),
            return_exceptions=True,
        )

    async def close(self) -> None:
        await asyncio.gather(
            *(state.client.close() for state in self._states),
            return_exceptions=True,
        )
