from __future__ import annotations

import asyncio
import time
import typing as t
from contextlib import suppress
from dataclasses import dataclass
from itertools import cycle

from pytoniq_core import Transaction

from tonutils.clients.base import BaseClient
from tonutils.clients.http.clients.quicknode import QuicknodeClient
from tonutils.exceptions import (
    BalancerError,
    ClientError,
    TransportError,
    ProviderError,
    ProviderResponseError,
    RunGetMethodError,
    ProviderTimeoutError,
    NotConnectedError,
)
from tonutils.types import ClientType, ContractInfo, NetworkGlobalID

_T = t.TypeVar("_T")


@dataclass
class HttpClientState:
    """Internal state for an HTTP client in the balancer.

    Attributes:
        client: Associated HTTP client.
        retry_after: Monotonic time before which requests are blocked, or `None`.
        error_count: Consecutive error count.
    """

    client: BaseClient
    retry_after: t.Optional[float] = None
    error_count: int = 0


class HttpBalancer(BaseClient):
    """Multi-provider HTTP client with automatic failover.

    Selects the best available HTTP client using limiter readiness,
    error counters, and round-robin tie-breaking.
    """

    TYPE = ClientType.HTTP

    def __init__(
        self,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        clients: t.List[BaseClient],
        request_timeout: float = 12.0,
    ) -> None:
        """
        :param network: Target TON network.
        :param clients: HTTP `BaseClient` instances to balance between.
        :param request_timeout: Total timeout in seconds including all failover attempts.
        """
        self.network = network

        self._clients: t.List[BaseClient] = []
        self._states: t.List[HttpClientState] = []
        self._init_clients(clients)

        self._rr = cycle(self._clients)

        self._retry_after_base = 1.0
        self._retry_after_max = 10.0

        self._request_timeout = request_timeout

    @property
    def connected(self) -> bool:
        """`True` if at least one HTTP client is connected."""
        return any(c.connected for c in self._clients)

    @property
    def provider(self) -> t.Any:
        """Provider of currently the best HTTP client."""
        c = self._pick_client()
        return c.provider

    async def connect(self) -> None:
        """Connect all registered clients."""
        await asyncio.gather(
            *(state.client.connect() for state in self._states),
            return_exceptions=True,
        )

    async def close(self) -> None:
        """Close all registered clients."""
        await asyncio.gather(
            *(state.client.close() for state in self._states),
            return_exceptions=True,
        )

    @property
    def clients(self) -> t.Tuple[BaseClient, ...]:
        """All registered HTTP clients."""
        return tuple(self._clients)

    @property
    def alive_clients(self) -> t.Tuple[BaseClient, ...]:
        """Connected clients not in cooldown."""
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if state.client.connected
            and (state.retry_after is None or state.retry_after <= now)
        )

    @property
    def dead_clients(self) -> t.Tuple[BaseClient, ...]:
        """Clients currently in cooldown."""
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if state.retry_after is not None and state.retry_after > now
        )

    def _init_clients(self, clients: t.List[BaseClient]) -> None:
        """Validate and register HTTP clients."""
        for client in clients:
            if client.TYPE != ClientType.HTTP:
                raise ClientError(
                    "HttpBalancer can work only with HTTP clients, "
                    f"got {client.__class__.__name__}."
                )

            if (
                isinstance(client, QuicknodeClient)
                and self.network == NetworkGlobalID.TESTNET
            ):
                raise ClientError(
                    "QuickNode HTTP client does not support testnet network."
                )

            client.network = self.network
            state = HttpClientState(client=client)

            self._clients.append(client)
            self._states.append(state)

    def _pick_client(self) -> BaseClient:
        """Select the best available HTTP client.

        Prefers lowest limiter wait time, then fewest errors,
        with round-robin fallback.
        """
        if not self.connected:
            raise NotConnectedError(component=self.__class__.__name__)

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
            raise BalancerError(
                "http balancer has no available clients (all in cooldown or not connected)"
            )

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
        """Reset error state for a successful client."""
        for state in self._states:
            if state.client is client:
                state.error_count = 0
                state.retry_after = None
                break

    def _mark_error(self, client: BaseClient, *, is_rate_limit: bool) -> None:
        """Update error state and schedule exponential-backoff cooldown.

        :param client: Client to penalize.
        :param is_rate_limit: Whether the error was rate-limit related.
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
        method: str,
    ) -> _T:
        """Execute a client operation with automatic failover.

        :param func: Async callable accepting a `BaseClient`.
        :param method: Operation name for error reporting.
        :return: Result of the first successful invocation.
        :raises BalancerError: If all clients fail.
        """

        async def _run() -> _T:
            if not self.connected:
                raise NotConnectedError(
                    component=self.__class__.__name__,
                    operation=method,
                )

            last_exc: t.Optional[BaseException] = None
            attempts = 0

            for _ in range(len(self._clients)):
                if not self.alive_clients:
                    break

                client = self._pick_client()
                attempts += 1

                try:
                    result = await func(client)
                except RunGetMethodError:
                    raise
                except ProviderResponseError as e:
                    self._mark_error(client, is_rate_limit=(e.code == 429))
                    last_exc = e
                    continue
                except (TransportError, ProviderError) as e:
                    self._mark_error(client, is_rate_limit=False)
                    last_exc = e
                    continue
                else:
                    self._mark_success(client)
                    return result

            if last_exc is None:
                raise BalancerError(
                    "http balancer has no available clients (all in cooldown or not connected)"
                )

            raise BalancerError(
                f"http failover exhausted after {attempts} attempt(s)"
            ) from last_exc

        try:
            return await asyncio.wait_for(_run(), timeout=self._request_timeout)
        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError(
                timeout=self._request_timeout,
                endpoint=self.__class__.__name__,
                operation="request",
            ) from exc

    async def _send_message(self, boc: str) -> None:
        async def _call(client: BaseClient) -> None:
            return await client._send_message(boc)

        method = "send_message"
        return await self._with_failover(_call, method)

    async def _get_config(self) -> t.Dict[int, t.Any]:
        async def _call(client: BaseClient) -> t.Dict[int, t.Any]:
            return await client._get_config()

        method = "get_config"
        return await self._with_failover(_call, method)

    async def _get_info(self, address: str) -> ContractInfo:
        async def _call(client: BaseClient) -> ContractInfo:
            return await client._get_info(address)

        method = "get_info"
        return await self._with_failover(_call, method)

    async def _get_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = None,
    ) -> t.List[Transaction]:
        async def _call(client: BaseClient) -> t.List[Transaction]:
            return await client._get_transactions(
                address=address,
                limit=limit,
                from_lt=from_lt,
                to_lt=to_lt,
            )

        method = "get_transactions"
        return await self._with_failover(_call, method)

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

        method = "run_get_method"
        return await self._with_failover(_call, method)
