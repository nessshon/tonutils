from __future__ import annotations

import asyncio
import time
import typing as t
from contextlib import suppress
from dataclasses import dataclass
from itertools import cycle

from pytoniq_core import Address, Transaction

from tonutils.clients.adnl.client import AdnlClient
from tonutils.clients.adnl.provider import AdnlProvider
from tonutils.clients.adnl.provider.config import TONClient
from tonutils.clients.adnl.provider.limiter import PriorityLimiter
from tonutils.clients.adnl.provider.models import GlobalConfig
from tonutils.clients.adnl.stack import decode_stack, encode_stack
from tonutils.clients.base import BaseClient
from tonutils.exceptions import (
    AdnlBalancerConnectionError,
    ClientNotConnectedError,
    RateLimitExceededError,
    ClientError,
)
from tonutils.types import ClientType, ContractStateInfo, NetworkGlobalID

_T = t.TypeVar("_T")


@dataclass
class AdnlClientState:
    """
    Internal state container for an ADNL client.

    Tracks error count and cooldown timeout for retry scheduling.
    """

    client: AdnlClient
    retry_after: t.Optional[float] = None
    error_count: int = 0


class AdnlBalancer(BaseClient):
    """
    Multi-provider ADNL client with automatic failover and load balancing.

    Selects the best available lite-server using height, ping metrics and
    round-robin tie-breaking.
    """

    TYPE = ClientType.ADNL

    def __init__(
        self,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        clients: t.List[AdnlClient],
        connect_timeout: int = 2,
    ) -> None:
        """
        Initialize ADNL balancer.

        It is recommended to build underlying AdnlClient instances from
        private lite-server configurations for better stability and performance.
        You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        Public free lite-server data may also be used via `from_network_config()`.

        :param network: Target TON network (mainnet or testnet)
        :param clients: List of AdnlClient instances to balance between
        :param connect_timeout: Timeout in seconds for connect/reconnect
        """
        self.network: NetworkGlobalID = network

        self._clients: t.List[AdnlClient] = []
        self._states: t.List[AdnlClientState] = []
        self.__init_clients(clients)

        self._rr = cycle(self._clients)
        self._connect_timeout = connect_timeout

        self._health_interval = 5.5
        self._health_task: t.Optional[asyncio.Task] = None

        self._retry_after_base = 1.0
        self._retry_after_max = 10.0

    def __init_clients(
        self,
        clients: t.List[AdnlClient],
    ) -> None:
        """
        Validate and register input ADNL clients.

        Ensures correct client type and network assignment.
        """
        for client in clients:
            if client.TYPE != ClientType.ADNL:
                raise ClientError(
                    "AdnlBalancer can work only with ADNL clients, "
                    f"got {client.__class__.__name__}."
                )

            client.network = self.network

            state = AdnlClientState(client=client)
            self._clients.append(client)
            self._states.append(state)

    @property
    def clients(self) -> t.Tuple[AdnlClient, ...]:
        """
        List of all registered ADNL clients.

        :return: Tuple of AdnlClient objects
        """
        return tuple(self._clients)

    @property
    def alive_clients(self) -> t.Tuple[AdnlClient, ...]:
        """
        ADNL clients that are allowed to send requests now.

        :return: Tuple of available AdnlClient instances
        """
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if state.client.is_connected
            and (state.retry_after is None or state.retry_after <= now)
        )

    @property
    def dead_clients(self) -> t.Tuple[AdnlClient, ...]:
        """
        ADNL clients currently in cooldown or disconnected.

        :return: Tuple of unavailable AdnlClient instances
        """
        now = time.monotonic()
        return tuple(
            state.client
            for state in self._states
            if not state.client.is_connected
            or (state.retry_after is not None and state.retry_after > now)
        )

    @property
    def provider(self) -> AdnlProvider:
        """
        Provider of the currently selected ADNL client.

        :return: AdnlProvider instance of chosen client
        :raises ClientNotConnectedError: If no clients are connected
        """
        if not self.is_connected:
            raise ClientNotConnectedError(self)
        c = self._pick_client()
        return c.provider

    @property
    def is_connected(self) -> bool:
        """
        Check whether at least one underlying ADNL client is connected.

        :return: True if any client is connected, otherwise False
        """
        return any(c.is_connected for c in self._clients)

    async def __aenter__(self) -> AdnlBalancer:
        """
        Enter async context manager and connect underlying clients.

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

    @classmethod
    def from_config(
        cls,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        config: t.Union[GlobalConfig, t.Dict[str, t.Any]],
        timeout: int = 10,
        connect_timeout: int = 2,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
        rps_per_provider: bool = False,
    ) -> AdnlBalancer:
        """
        Build ADNL balancer from a lite-server config.

        For best performance, it is recommended to use a private lite-server
        configuration. You can obtain private configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        Public free configs may also be used via `from_network_config()`.

        :param network: Target TON network
        :param config: GlobalConfig instance or raw dict
        :param timeout: Lite-server request timeout in seconds
        :param connect_timeout: Timeout in seconds for connect/reconnect attempts
        :param rps_limit: Optional shared requests-per-second limit
        :param rps_period: Time window in seconds for RPS limit
        :param rps_retries: Number of retries on rate limiting
        :param rps_per_provider: Whether to create per-provider limiters
        :return: Configured AdnlBalancer instance
        """
        if isinstance(config, dict):
            config = GlobalConfig(**config)

        shared_limiter: t.Optional[PriorityLimiter] = None
        if rps_limit is not None and not rps_per_provider:
            shared_limiter = PriorityLimiter(rps_limit, rps_period)

        clients: t.List[AdnlClient] = []
        for node in config.liteservers:
            if rps_per_provider:
                _limiter = (
                    PriorityLimiter(rps_limit, rps_period)
                    if rps_limit is not None
                    else None
                )
                _rps_limit = rps_limit
            else:
                _limiter = shared_limiter
                _rps_limit = None

            client = AdnlClient(
                network=network,
                ip=node.host,
                port=node.port,
                public_key=node.id,
                timeout=timeout,
                rps_limit=_rps_limit,
                rps_retries=rps_retries,
                rps_period=rps_period,
                limiter=_limiter,
            )
            clients.append(client)

        return cls(
            network=network,
            clients=clients,
            connect_timeout=connect_timeout,
        )

    @classmethod
    async def from_network_config(
        cls,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        timeout: int = 10,
        connect_timeout: int = 2,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
        rps_per_provider: bool = False,
    ) -> AdnlBalancer:
        """
        Build ADNL balancer using global config fetched from ton.org.

        Public lite-servers available in the global network configuration are
        free to use but may be unstable under load. For higher reliability and
        performance, it is recommended to use private lite-server configurations,
        available from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        :param network: Target TON network
        :param timeout: Lite-server request timeout in seconds
        :param connect_timeout: Timeout in seconds for connect/reconnect attempts
        :param rps_limit: Optional shared requests-per-second limit
        :param rps_period: Time window in seconds for RPS limit
        :param rps_retries: Number of retries on rate limiting
        :param rps_per_provider: Whether to create per-provider limiters
        :return: Configured AdnlBalancer instance
        """
        ton_client = TONClient()
        config_getters = {
            NetworkGlobalID.MAINNET: ton_client.mainnet_global_config,
            NetworkGlobalID.TESTNET: ton_client.testnet_global_config,
        }
        async with ton_client:
            config = await config_getters[network]()
        return cls.from_config(
            network=network,
            config=config,
            timeout=timeout,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
            rps_per_provider=rps_per_provider,
            connect_timeout=connect_timeout,
        )

    def _pick_client(self) -> AdnlClient:
        """
        Select the best available ADNL client.

        Selection criteria:
        - highest known masterchain seqno
        - minimal ping RTT and age among same-height clients
        - round-robin fallback if no height information
        """
        alive_clients = list(self.alive_clients)

        if not alive_clients:
            raise AdnlBalancerConnectionError("No alive lite-server clients available.")

        height_candidates: t.List[
            t.Tuple[
                int,
                t.Optional[float],
                t.Optional[float],
                AdnlClient,
            ]
        ] = []

        for client in alive_clients:
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
            if candidate in alive_clients and candidate.is_connected:
                return candidate

        return alive_clients[0]

    def _mark_success(self, client: AdnlClient) -> None:
        """
        Reset error state for a successful client.

        Clears cooldown and error counters.
        """
        for state in self._states:
            if state.client is client:
                state.error_count = 0
                state.retry_after = None
                break

    def _mark_error(self, client: AdnlClient, is_rate_limit: bool) -> None:
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
        func: t.Callable[[AdnlProvider], t.Awaitable[_T]],
    ) -> _T:
        """
        Execute a provider operation with automatic failover.

        Iterates through available lite-servers until one succeeds
        or all providers fail.

        :param func: Callable performing an operation using an AdnlProvider
        :return: Result of the successful invocation
        """
        last_exc: t.Optional[BaseException] = None

        for _ in range(len(self._clients)):
            if not self.alive_clients:
                break

            client = self._pick_client()

            if not client.provider.is_connected:
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
            except RateLimitExceededError as e:
                self._mark_error(client, is_rate_limit=True)
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

        raise AdnlBalancerConnectionError(
            "All lite-server providers failed to process request"
        )

    async def _send_boc(self, boc: str) -> None:
        async def _call(provider: AdnlProvider) -> None:
            return await provider.send_message(bytes.fromhex(boc))

        return await self._with_failover(_call)

    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        async def _call(provider: AdnlProvider) -> t.Dict[int, t.Any]:
            return await provider.get_config_all()

        return await self._with_failover(_call)

    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        async def _call(provider: AdnlProvider) -> ContractStateInfo:
            return await provider.get_account_state(Address(address))

        return await self._with_failover(_call)

    async def _get_contract_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: int = 0,
    ) -> t.List[Transaction]:
        state = await self._get_contract_info(address)
        account = Address(address).to_tl_account_id()

        if state.last_transaction_lt is None or state.last_transaction_hash is None:
            return []

        curr_lt = state.last_transaction_lt
        curr_hash = state.last_transaction_hash
        transactions: list[Transaction] = []

        while len(transactions) < limit and curr_lt != 0:
            batch_size = min(16, limit - len(transactions))

            async def _call(provider: AdnlProvider) -> list[Transaction]:
                return await provider.get_transactions(
                    account=account,
                    count=batch_size,
                    from_lt=curr_lt,
                    from_hash=curr_hash,
                )

            txs = await self._with_failover(_call)
            if not txs:
                break

            if to_lt > 0 and txs[-1].lt <= to_lt:
                trimmed: list[Transaction] = []
                for tx in txs:
                    if tx.lt <= to_lt:
                        break
                    trimmed.append(tx)
                transactions.extend(trimmed)
                break

            transactions.extend(txs)

            last_tx = txs[-1]
            curr_lt = last_tx.prev_trans_lt
            curr_hash = last_tx.prev_trans_hash.hex()

        return (
            [tx for tx in transactions if tx.lt < from_lt]
            if from_lt is not None
            else transactions
        )

    async def _run_get_method(
        self,
        address: str,
        method_name: str,
        stack: t.Optional[t.List[t.Any]] = None,
    ) -> t.List[t.Any]:
        async def _call(provider: AdnlProvider) -> t.List[t.Any]:
            result = await provider.run_smc_method(
                address=Address(address),
                method_name=method_name,
                stack=encode_stack(stack or []),
            )
            return decode_stack(result or [])

        return await self._with_failover(_call)

    def _ensure_health_task(self) -> None:
        if self._health_task is not None and not self._health_task.done():
            return

        loop = asyncio.get_running_loop()
        self._health_task = loop.create_task(
            self._health_loop(),
            name="_health_loop",
        )

    async def _health_loop(self) -> None:

        async def _recon(c: AdnlClient) -> None:
            with suppress(Exception):
                await asyncio.wait_for(
                    c.reconnect(),
                    timeout=self._connect_timeout,
                )

        try:
            while True:
                await asyncio.sleep(self._health_interval)
                tasks = [
                    _recon(client)
                    for client in self.dead_clients
                    if not client.is_connected
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            return

    async def connect(self) -> None:
        if self.is_connected:
            self._ensure_health_task()
            return

        async def _con(client: AdnlClient) -> None:
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(
                    client.connect(),
                    timeout=self._connect_timeout,
                )

        tasks = [_con(client) for client in self._clients]
        await asyncio.gather(*tasks, return_exceptions=True)

        if self.is_connected:
            self._ensure_health_task()
            return

        raise AdnlBalancerConnectionError(
            "All lite-servers failed to establish connection."
        )

    async def close(self) -> None:
        task, self._health_task = self._health_task, None

        if task is not None and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        tasks = [client.close() for client in self._clients]
        await asyncio.gather(*tasks, return_exceptions=True)
