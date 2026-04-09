from __future__ import annotations

import asyncio
import time
import typing as t
from contextlib import suppress
from dataclasses import dataclass
from itertools import cycle

from ton_core import (
    GlobalConfig,
    NetworkGlobalID,
    get_mainnet_global_config,
    get_testnet_global_config,
)

from tonutils.clients.base import BaseClient
from tonutils.clients.config import resolve_config
from tonutils.clients.lite.client import LiteClient
from tonutils.clients.lite.mixin import LiteMixin
from tonutils.exceptions import (
    BalancerError,
    ClientError,
    NetworkNotSupportedError,
    NotConnectedError,
    ProviderError,
    ProviderResponseError,
    ProviderTimeoutError,
    RunGetMethodError,
    TransportError,
)
from tonutils.transports.limiter import RateLimiter
from tonutils.types import (
    LITESERVER_RATE_LIMIT_CODES,
    ClientType,
    RetryPolicy,
)

if t.TYPE_CHECKING:
    from tonutils.providers.lite import LiteProvider

_T = t.TypeVar("_T")


@dataclass
class LiteClientState:
    """Internal state for a lite-server client in the balancer."""

    client: LiteClient
    """Associated lite-server client."""

    retry_after: float | None = None
    """Monotonic time before which requests are blocked, or ``None``."""

    error_count: int = 0
    """Consecutive error count."""


class LiteBalancer(LiteMixin, BaseClient):
    """Multi-client lite-server balancer with automatic failover.

    Selects the best available lite-server using masterchain height,
    ping RTT, and round-robin tie-breaking.
    """

    TYPE = ClientType.ADNL

    def __init__(
        self,
        network: NetworkGlobalID,
        *,
        clients: list[LiteClient],
        connect_timeout: float = 2.0,
        request_timeout: float = 12.0,
    ) -> None:
        """Initialize the balancer.

        :param network: Target TON network.
        :param clients: ``LiteClient`` instances to balance between.
        :param connect_timeout: Timeout in seconds for connect/reconnect attempts.
        :param request_timeout: Total timeout in seconds including all failover attempts.
        """
        self.network: NetworkGlobalID = network

        self._clients: list[LiteClient] = []
        self._states: list[LiteClientState] = []
        self._init_clients(clients)

        self._rr = cycle(self._clients)

        self._connect_timeout = connect_timeout
        self._request_timeout = request_timeout

        self._health_interval = 5.5
        self._health_task: asyncio.Task[None] | None = None

        self._retry_after_base = 1.0
        self._retry_after_max = 10.0

    @property
    def provider(self) -> LiteProvider:
        """Provider of the currently best lite-server client."""
        c = self._pick_client()
        return c.provider

    @property
    def connected(self) -> bool:
        """``True`` if at least one lite-server client is connected."""
        return any(c.connected for c in self._clients)

    @property
    def clients(self) -> tuple[LiteClient, ...]:
        """All registered lite-server clients."""
        return tuple(self._clients)

    @property
    def alive_clients(self) -> tuple[LiteClient, ...]:
        """Connected clients not in cooldown."""
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if state.client.connected and (state.retry_after is None or state.retry_after <= now)
        )

    @property
    def dead_clients(self) -> tuple[LiteClient, ...]:
        """Disconnected or cooldown clients."""
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if not state.client.connected or (state.retry_after is not None and state.retry_after > now)
        )

    @classmethod
    def from_config(
        cls,
        network: NetworkGlobalID,
        *,
        config: GlobalConfig | dict[str, t.Any] | str,
        connect_timeout: float = 2.0,
        request_timeout: float = 12.0,
        client_connect_timeout: float = 1.5,
        client_request_timeout: float = 5.0,
        rps_limit: int | None = None,
        rps_period: float = 1.0,
        rps_per_client: bool = False,
        retry_policy: RetryPolicy | None = None,
    ) -> LiteBalancer:
        """Create a ``LiteBalancer`` from a configuration.

        For best performance, it is recommended to use a private lite-server
        configuration. You can obtain private configs from:
            - Tonconsole website: https://tonconsole.com/.
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/).
        Public free configs may also be used via ``from_network_config()``.

        :param network: Target TON network.
        :param config: ``GlobalConfig``, file path, or raw dict.
        :param connect_timeout: Balancer failover connect timeout in seconds.
        :param request_timeout: Total timeout in seconds including all failover attempts.
        :param client_connect_timeout: Per-client connect/handshake timeout in seconds.
        :param client_request_timeout: Per-client single request timeout in seconds.
        :param rps_limit: Requests-per-second limit, or ``None``.
        :param rps_period: Time window in seconds for RPS limit.
        :param rps_per_client: Create per-client limiters instead of shared.
        :param retry_policy: Retry policy with per-error-code rules, or ``None``.
        :return: Configured ``LiteBalancer`` instance.
        """
        config = resolve_config(config)

        shared_limiter: RateLimiter | None = None
        if rps_limit is not None and not rps_per_client:
            shared_limiter = RateLimiter(rps_limit, rps_period)

        clients: list[LiteClient] = []
        for ls in config.liteservers:
            limiter = RateLimiter(rps_limit, rps_period) if rps_per_client and rps_limit is not None else shared_limiter
            client_rps_limit = rps_limit if rps_per_client else None

            clients.append(
                LiteClient(
                    network=network,
                    ip=ls.host,
                    port=ls.port,
                    public_key=ls.pub_key,
                    connect_timeout=client_connect_timeout,
                    request_timeout=client_request_timeout,
                    rps_limit=client_rps_limit,
                    rps_period=rps_period,
                    limiter=limiter,
                    retry_policy=retry_policy,
                )
            )

        return cls(
            network=network,
            clients=clients,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
        )

    @classmethod
    def from_network_config(
        cls,
        network: NetworkGlobalID,
        *,
        connect_timeout: float = 2.0,
        request_timeout: float = 12.0,
        client_connect_timeout: float = 1.5,
        client_request_timeout: float = 5.0,
        rps_limit: int | None = None,
        rps_period: float = 1.0,
        rps_per_client: bool = False,
        retry_policy: RetryPolicy | None = None,
    ) -> LiteBalancer:
        """Create a ``LiteBalancer`` using global config from ton.org.

        Public lite-servers available in the global network configuration are
        free to use but may be unstable under load. For higher reliability and
        performance, it is recommended to use private lite-server configurations,
        available from:
            - Tonconsole website: https://tonconsole.com/.
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/).

        :param network: Target TON network.
        :param connect_timeout: Balancer failover connect timeout in seconds.
        :param request_timeout: Total timeout in seconds including all failover attempts.
        :param client_connect_timeout: Per-client connect/handshake timeout in seconds.
        :param client_request_timeout: Per-client single request timeout in seconds.
        :param rps_limit: Requests-per-second limit, or ``None``.
        :param rps_period: Time window in seconds for RPS limit.
        :param rps_per_client: Create per-client limiters instead of shared.
        :param retry_policy: Retry policy with per-error-code rules, or ``None``.
        :return: Configured ``LiteBalancer`` instance.
        """
        config_getters = {
            NetworkGlobalID.MAINNET: get_mainnet_global_config,
            NetworkGlobalID.TESTNET: get_testnet_global_config,
        }
        getter = config_getters.get(network)
        if getter is None:
            raise NetworkNotSupportedError(network, provider="LiteBalancer")
        config = getter()
        return cls.from_config(
            network=network,
            config=config,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
            client_connect_timeout=client_connect_timeout,
            client_request_timeout=client_request_timeout,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_per_client=rps_per_client,
            retry_policy=retry_policy,
        )

    async def connect(self) -> None:
        """Connect all clients and start the health check task."""
        if self.connected:
            self._ensure_health_task()
            return

        async def _con(client: LiteClient) -> None:
            with suppress(Exception):
                await asyncio.wait_for(
                    client.connect(),
                    timeout=self._connect_timeout,
                )

        tasks = [_con(client) for client in self._clients]
        await asyncio.gather(*tasks, return_exceptions=True)

        if any(c.connected for c in self._clients):
            self._ensure_health_task()
            return

        raise BalancerError(
            "all lite-servers failed to establish connection",
            hint="Check network connectivity or try a different global config.",
        )

    async def close(self) -> None:
        """Stop the health check task and close all clients."""
        task, self._health_task = self._health_task, None

        if task is not None and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        tasks = [client.close() for client in self._clients]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _init_clients(
        self,
        clients: list[LiteClient],
    ) -> None:
        """Validate and register lite-server clients."""
        for client in clients:
            if client.TYPE != ClientType.ADNL:
                raise ClientError(
                    f"{self.__class__.__name__} can work only with LiteClient instances, "
                    f"got {client.__class__.__name__}."
                )

            client.network = self.network

            state = LiteClientState(client=client)
            self._clients.append(client)
            self._states.append(state)

    def _pick_client(self) -> LiteClient:
        """Select the best available lite-server client.

        Prefers highest masterchain seqno, then lowest ping RTT,
        with round-robin fallback.
        """
        if not self.connected:
            raise NotConnectedError(component=self.__class__.__name__)

        alive = list(self.alive_clients)

        if not alive:
            raise BalancerError(
                "no alive lite-servers available",
                hint="Servers may be overloaded or unreachable. Wait and retry, or add more servers.",
            )

        height_candidates: list[
            tuple[
                int,
                float | None,
                float | None,
                LiteClient,
            ]
        ] = []

        for client in alive:
            mc_block = client.provider.last_mc_block
            if mc_block is None:
                continue
            seqno = mc_block.seqno
            rtt = client.provider.last_ping_rtt
            age = client.provider.last_ping_age
            height_candidates.append((seqno, rtt, age, client))

        if height_candidates:
            max_seqno = max(item[0] for item in height_candidates)
            same_height = [item for item in height_candidates if item[0] == max_seqno]
            with_ping = [item for item in same_height if item[1] is not None and item[2] is not None]
            if with_ping:
                with_ping.sort(key=lambda x: (x[1], x[2]))
                return with_ping[0][3]
            return same_height[0][3]

        for _ in range(len(self._clients)):
            candidate = next(self._rr)
            if candidate in alive and candidate.connected:
                return candidate

        return alive[0]

    def _mark_success(self, client: LiteClient) -> None:
        """Reset error state for a successful client."""
        for state in self._states:
            if state.client is client:
                state.error_count = 0
                state.retry_after = None
                break

    def _mark_error(self, client: LiteClient, is_rate_limit: bool) -> None:
        """Update error state and schedule exponential-backoff cooldown.

        :param client: Client to penalize.
        :param is_rate_limit: Whether the error was rate-limit related.
        """
        now = time.monotonic()
        for state in self._states:
            if state.client is client:
                state.error_count += 1
                base = self._retry_after_base if is_rate_limit else self._retry_after_base / 2
                cooldown = min(
                    base * (2 ** (state.error_count - 1)),
                    self._retry_after_max,
                )
                state.retry_after = now + cooldown
                break

    def _ensure_health_task(self) -> None:
        """Start the background health check task if not already running."""
        if self._health_task is not None and not self._health_task.done():
            return

        loop = asyncio.get_running_loop()
        self._health_task = loop.create_task(
            self._health_loop(),
            name="_health_loop",
        )

    async def _health_loop(self) -> None:
        """Periodically reconnect dead lite-server clients until cancelled."""

        async def _recon(c: LiteClient) -> None:
            with suppress(Exception):
                await asyncio.wait_for(
                    c.provider.reconnect(),
                    timeout=self._connect_timeout,
                )

        try:
            while True:
                await asyncio.sleep(self._health_interval)
                tasks = [_recon(client) for client in self.dead_clients if not client.connected]
                await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            return

    async def _with_failover(
        self,
        func: t.Callable[[LiteProvider], t.Awaitable[_T]],
    ) -> _T:
        """Execute a provider operation with automatic failover.

        :param func: Async callable accepting a ``LiteProvider``.
        :return: Result of the first successful invocation.
        :raises BalancerError: If all lite-servers fail.
        """

        async def _run() -> _T:
            last_exc: BaseException | None = None
            attempts = 0

            for _ in range(len(self._clients)):
                if not self.alive_clients:
                    break

                client = self._pick_client()
                attempts += 1

                if not client.provider.connected:
                    self._mark_error(client, is_rate_limit=False)
                    continue

                try:
                    result = await func(client.provider)

                except RunGetMethodError:
                    raise
                except ProviderResponseError as e:
                    is_rate_limit = e.code in LITESERVER_RATE_LIMIT_CODES
                    self._mark_error(client, is_rate_limit=is_rate_limit)
                    last_exc = e
                    continue
                except (TransportError, ProviderError) as e:
                    self._mark_error(client, is_rate_limit=False)
                    last_exc = e
                    continue

                self._mark_success(client)
                return result

            if last_exc is not None:
                raise BalancerError(
                    f"lite failover exhausted after {attempts} attempt(s): {last_exc}",
                    hint="Reduce request rate or add more lite-servers to the balancer.",
                ) from last_exc
            raise BalancerError(
                "no alive lite-servers available",
                hint="Servers may be overloaded or unreachable. Wait and retry, or add more servers.",
            )

        try:
            return await asyncio.wait_for(_run(), timeout=self._request_timeout)
        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError(
                timeout=self._request_timeout,
                endpoint=self.__class__.__name__,
                operation="failover request",
            ) from exc

    async def _adnl_call(self, method: str, /, *args: t.Any, **kwargs: t.Any) -> t.Any:
        """Execute a provider call with failover across lite-servers.

        :param method: Provider method name.
        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Provider method result.
        """
        if not self.connected:
            raise NotConnectedError(
                component=self.__class__.__name__,
                operation=method,
            )

        async def _call(provider: LiteProvider) -> t.Any:
            fn = getattr(provider, method)
            return await fn(*args, **kwargs)

        return await self._with_failover(_call)
