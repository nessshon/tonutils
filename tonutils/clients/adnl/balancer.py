from __future__ import annotations

import asyncio
import time
import typing as t
from contextlib import suppress
from dataclasses import dataclass
from itertools import cycle

from tonutils.clients.adnl.client import LiteClient
from tonutils.clients.adnl.mixin import LiteMixin
from tonutils.clients.adnl.provider import AdnlProvider
from tonutils.clients.adnl.provider.config import (
    get_mainnet_global_config,
    get_testnet_global_config,
    load_global_config,
)
from tonutils.clients.adnl.provider.models import GlobalConfig
from tonutils.clients.base import BaseClient
from tonutils.clients.limiter import RateLimiter
from tonutils.exceptions import (
    ClientError,
    BalancerError,
    RunGetMethodError,
    NotConnectedError,
    ProviderResponseError,
    TransportError,
    ProviderError,
    ProviderTimeoutError,
)
from tonutils.types import (
    ClientType,
    NetworkGlobalID,
    RetryPolicy,
)

_T = t.TypeVar("_T")


@dataclass
class LiteClientState:
    """
    Internal state container for a lite-server client.

    Tracks error count and cooldown timeout for retry scheduling.
    """

    client: LiteClient
    retry_after: t.Optional[float] = None
    error_count: int = 0


class LiteBalancer(LiteMixin, BaseClient):
    """
    Multi-client lite-server balancer with automatic failover and load balancing.

    Selects the best available lite-server using height, ping metrics and
    round-robin tie-breaking.
    """

    TYPE = ClientType.ADNL

    def __init__(
        self,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        clients: t.List[LiteClient],
        connect_timeout: float = 2.0,
        request_timeout: float = 12.0,
    ) -> None:
        """
        Initialize lite-server balancer.

        It is recommended to build underlying LiteClient instances from
        private lite-server configurations for better stability and performance.
        You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        Public free lite-server data may also be used via `from_network_config()`.

        :param network: Target TON network (mainnet or testnet)
        :param clients: List of LiteClient instances to balance between
        :param connect_timeout: Timeout in seconds for connect/reconnect attempts
        :param request_timeout: Maximum total time in seconds for a balancer operation,
            including all failover attempts across lite-servers
        """
        self.network: NetworkGlobalID = network

        self._clients: t.List[LiteClient] = []
        self._states: t.List[LiteClientState] = []
        self._init_clients(clients)

        self._rr = cycle(self._clients)

        self._connect_timeout = connect_timeout
        self._request_timeout = request_timeout

        self._health_interval = 5.5
        self._health_task: t.Optional[asyncio.Task] = None

        self._retry_after_base = 1.0
        self._retry_after_max = 10.0

    @property
    def provider(self) -> AdnlProvider:
        """
        Provider of the currently selected lite-server client.

        :return: AdnlProvider instance of chosen client
        """
        c = self._pick_client()
        return c.provider

    @property
    def connected(self) -> bool:
        """
        Check whether at least one underlying lite-server client is connected.

        :return: True if any client is connected, otherwise False
        """
        return any(c.connected for c in self._clients)

    @property
    def clients(self) -> t.Tuple[LiteClient, ...]:
        """
        List of all registered lite-server clients.

        :return: Tuple of LiteClient objects
        """
        return tuple(self._clients)

    @property
    def alive_clients(self) -> t.Tuple[LiteClient, ...]:
        """
        Lite-server clients that are allowed to send requests now.

        :return: Tuple of available LiteClient instances
        """
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if state.client.connected
            and (state.retry_after is None or state.retry_after <= now)
        )

    @property
    def dead_clients(self) -> t.Tuple[LiteClient, ...]:
        """
        Lite-server clients currently in cooldown or disconnected.

        :return: Tuple of unavailable LiteClient instances
        """
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if not state.client.connected
            or (state.retry_after is not None and state.retry_after > now)
        )

    @classmethod
    def from_config(
        cls,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        config: t.Union[GlobalConfig, t.Dict[str, t.Any], str],
        connect_timeout: float = 2.0,
        request_timeout: float = 12.0,
        client_connect_timeout: float = 1.5,
        client_request_timeout: float = 5.0,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_per_client: bool = False,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> LiteBalancer:
        """
        Build lite-server balancer from a configuration.

        For best performance, it is recommended to use a private lite-server
        configuration. You can obtain private configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        Public free configs may also be used via `from_network_config()`.

        :param network: Target TON network
        :param config: GlobalConfig instance, config file path as string, or raw dict
        :param connect_timeout: Timeout in seconds for a single connect/reconnect attempt
            performed by the balancer during failover.
        :param request_timeout: Maximum total time in seconds for a single balancer operation,
            including all failover attempts across clients.
        :param client_connect_timeout: Timeout in seconds for connect/handshake performed by an
            individual lite-server client.
        :param client_request_timeout: Timeout in seconds for a single request executed by an
            individual lite-server client.
        :param rps_limit: Optional requests-per-second limit
        :param rps_period: Time window in seconds for RPS limit
        :param rps_per_client: Whether to create per-client limiters
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        :return: Configured LiteBalancer instance
        """
        if isinstance(config, str):
            config = load_global_config(config)
        if isinstance(config, dict):
            config = GlobalConfig(**config)

        shared_limiter: t.Optional[RateLimiter] = None
        if rps_limit is not None and not rps_per_client:
            shared_limiter = RateLimiter(rps_limit, rps_period)

        clients: t.List[LiteClient] = []
        for ls in config.liteservers:
            limiter = (
                RateLimiter(rps_limit, rps_period)
                if rps_per_client and rps_limit is not None
                else shared_limiter
            )
            client_rps_limit = rps_limit if rps_per_client else None

            clients.append(
                LiteClient(
                    network=network,
                    ip=ls.host,
                    port=ls.port,
                    public_key=ls.id,
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
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        connect_timeout: float = 2.0,
        request_timeout: float = 12.0,
        client_connect_timeout: float = 1.5,
        client_request_timeout: float = 5.0,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_per_client: bool = False,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> LiteBalancer:
        """
        Build lite-server balancer using global config fetched from ton.org.

        Public lite-servers available in the global network configuration are
        free to use but may be unstable under load. For higher reliability and
        performance, it is recommended to use private lite-server configurations,
        available from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        :param network: Target TON network
        :param connect_timeout: Timeout in seconds for a single connect/reconnect attempt
            performed by the balancer during failover.
        :param request_timeout: Maximum total time in seconds for a single balancer operation,
            including all failover attempts across clients.
        :param client_connect_timeout: Timeout in seconds for connect/handshake performed by an
            individual lite-server client.
        :param client_request_timeout: Timeout in seconds for a single request executed by an
            individual lite-server client.
        :param rps_limit: Optional requests-per-second limit
        :param rps_period: Time window in seconds for RPS limit
        :param rps_per_client: Whether to create per-client limiters
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        :return: Configured LiteBalancer instance
        """
        config_getters = {
            NetworkGlobalID.MAINNET: get_mainnet_global_config,
            NetworkGlobalID.TESTNET: get_testnet_global_config,
        }
        config = config_getters[network]()
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

        if self.connected:
            self._ensure_health_task()
            return

        raise BalancerError("all lite-servers failed to establish connection")

    async def close(self) -> None:
        task, self._health_task = self._health_task, None

        if task is not None and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        tasks = [client.close() for client in self._clients]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _init_clients(
        self,
        clients: t.List[LiteClient],
    ) -> None:
        """
        Validate and register input lite-server clients.

        Ensures correct client type and network assignment.
        """
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
        """
        Select the best available lite-server client.

        Selection criteria:
        - highest known masterchain seqno
        - minimal ping RTT and age among same-height clients
        - round-robin fallback if no height information
        """
        if not self.connected:
            raise NotConnectedError(component=self.__class__.__name__)

        alive = list(self.alive_clients)

        if not alive:
            raise BalancerError("no alive lite-servers available")

        height_candidates: t.List[
            t.Tuple[
                int,
                t.Optional[float],
                t.Optional[float],
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
            with_ping = [
                item
                for item in same_height
                if item[1] is not None and item[2] is not None
            ]
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
        """
        Reset error state for a successful client.

        Clears cooldown and error counters.
        """
        for state in self._states:
            if state.client is client:
                state.error_count = 0
                state.retry_after = None
                break

    def _mark_error(self, client: LiteClient, is_rate_limit: bool) -> None:
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

    def _ensure_health_task(self) -> None:
        """
        Ensure background health check task is running.

        Starts a periodic reconnect loop for unavailable clients
        if it is not already active.
        """
        if self._health_task is not None and not self._health_task.done():
            return

        loop = asyncio.get_running_loop()
        self._health_task = loop.create_task(
            self._health_loop(),
            name="_health_loop",
        )

    async def _health_loop(self) -> None:
        """
        Periodically attempt to reconnect dead lite-server clients.

        Runs until cancelled.
        """

        async def _recon(c: LiteClient) -> None:
            with suppress(Exception):
                await asyncio.wait_for(
                    c.provider.reconnect(),
                    timeout=self._connect_timeout,
                )

        try:
            while True:
                await asyncio.sleep(self._health_interval)
                tasks = [
                    _recon(client)
                    for client in self.dead_clients
                    if not client.connected
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            return

    async def _with_failover(
        self,
        func: t.Callable[[AdnlProvider], t.Awaitable[_T]],
    ) -> _T:
        """
        Execute a provider operation with automatic failover.

        Iterates through available lite-servers until one succeeds
        or all fail.

        :param func: Callable performing an operation using an AdnlProvider
        :return: Result of the successful invocation
        """

        async def _run() -> _T:
            last_exc: t.Optional[BaseException] = None

            for _ in range(len(self._clients)):
                if not self.alive_clients:
                    break

                client = self._pick_client()

                if not client.provider.connected:
                    try:
                        await asyncio.wait_for(
                            client.provider.reconnect(),
                            timeout=self._connect_timeout,
                        )
                    except Exception as e:
                        self._mark_error(client, is_rate_limit=False)
                        last_exc = e
                        continue

                try:
                    result = await func(client.provider)

                except RunGetMethodError:
                    raise
                except ProviderResponseError as e:
                    is_rate_limit = e.code in {228, 5556}
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
                raise BalancerError("lite failover exhausted") from last_exc
            raise BalancerError("no alive lite-servers available")

        try:
            return await asyncio.wait_for(_run(), timeout=self._request_timeout)
        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError(
                timeout=self._request_timeout,
                endpoint=self.__class__.__name__,
                operation="failover request",
            ) from exc

    async def _adnl_call(self, method: str, /, *args: t.Any, **kwargs: t.Any) -> t.Any:
        """
        Execute lite-server call with failover across providers.

        :param method: Provider coroutine method name.
        :param args: Positional arguments forwarded to the provider method.
        :param kwargs: Keyword arguments forwarded to the provider method.
        :return: Provider method result.
        """
        if not self.connected:
            raise NotConnectedError(
                component=self.__class__.__name__,
                operation=method,
            )

        async def _call(provider: AdnlProvider) -> t.Any:
            fn = getattr(provider, method)
            return await fn(*args, **kwargs)

        return await self._with_failover(_call)
