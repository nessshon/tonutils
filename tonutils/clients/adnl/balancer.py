from __future__ import annotations

import asyncio
import time
import typing as t
from contextlib import suppress
from dataclasses import dataclass
from itertools import cycle

from pytoniq_core import Address, BlockIdExt, Block, Transaction

from tonutils.clients.adnl.client import LiteClient
from tonutils.clients.adnl.provider import AdnlProvider
from tonutils.clients.adnl.provider.config import (
    get_mainnet_global_config,
    get_testnet_global_config,
)
from tonutils.clients.adnl.provider.models import GlobalConfig, MasterchainInfo
from tonutils.clients.adnl.utils import decode_stack, encode_stack
from tonutils.clients.base import BaseClient
from tonutils.clients.limiter import RateLimiter
from tonutils.exceptions import (
    ClientError,
    BalancerError,
    RunGetMethodError,
    ProviderResponseError,
    TransportError,
    ProviderError,
    ProviderTimeoutError,
)
from tonutils.types import (
    ClientType,
    ContractStateInfo,
    NetworkGlobalID,
    RetryPolicy,
    WorkchainID,
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


class LiteBalancer(BaseClient):
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
        self.__init_clients(clients)

        self._rr = cycle(self._clients)

        self._connect_timeout = connect_timeout
        self._request_timeout = request_timeout

        self._health_interval = 5.5
        self._health_task: t.Optional[asyncio.Task] = None

        self._retry_after_base = 1.0
        self._retry_after_max = 10.0

    def __init_clients(
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
                    "LiteBalancer can work only with LiteClient instances, "
                    f"got {client.__class__.__name__}."
                )

            client.network = self.network

            state = LiteClientState(client=client)
            self._clients.append(client)
            self._states.append(state)

    @property
    def provider(self) -> AdnlProvider:
        """
        Provider of the currently selected lite-server client.

        :return: AdnlProvider instance of chosen client
        """
        c = self._pick_client()
        return c.provider

    @property
    def is_connected(self) -> bool:
        """
        Check whether at least one underlying lite-server client is connected.

        :return: True if any client is connected, otherwise False
        """
        return any(c.is_connected for c in self._clients)

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
            if state.client.is_connected
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
            if not state.client.is_connected
            or (state.retry_after is not None and state.retry_after > now)
        )

    async def __aenter__(self) -> LiteBalancer:
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
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        config: t.Union[GlobalConfig, t.Dict[str, t.Any]],
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
        :param config: GlobalConfig instance or raw dict
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

    def _pick_client(self) -> LiteClient:
        """
        Select the best available lite-server client.

        Selection criteria:
        - highest known masterchain seqno
        - minimal ping RTT and age among same-height clients
        - round-robin fallback if no height information
        """
        alive = list(self.alive_clients)

        if not alive:
            raise BalancerError("no alive lite-server clients available")

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
            if candidate in alive and candidate.is_connected:
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
                raise last_exc

            raise BalancerError("all lite-servers failed to process request")

        try:
            return await asyncio.wait_for(_run(), timeout=self._request_timeout)
        except asyncio.TimeoutError as exc:
            raise ProviderTimeoutError(
                timeout=self._request_timeout,
                endpoint="lite balancer",
                operation="failover request",
            ) from exc

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

    async def _get_transactions(
        self,
        address: str,
        limit: int = 100,
        from_lt: t.Optional[int] = None,
        to_lt: t.Optional[int] = None,
    ) -> t.List[Transaction]:
        to_lt = 0 if to_lt is None else to_lt
        state = await self._get_contract_info(address)
        account = Address(address).to_tl_account_id()

        if state.last_transaction_lt is None or state.last_transaction_hash is None:
            return []

        curr_lt = state.last_transaction_lt
        curr_hash = state.last_transaction_hash
        transactions: t.List[Transaction] = []

        while curr_lt != 0:
            fetch_lt = curr_lt
            fetch_hash = curr_hash

            async def _call(provider: AdnlProvider) -> t.List[Transaction]:
                return await provider.get_transactions(
                    account=account,
                    count=16,
                    from_lt=fetch_lt,
                    from_hash=fetch_hash,
                )

            txs = await self._with_failover(_call)
            if not txs:
                break

            for tx in txs:
                if from_lt is not None and tx.lt > from_lt:
                    continue
                if to_lt > 0 and tx.lt <= to_lt:
                    return transactions[:limit]

                transactions.append(tx)
                if len(transactions) >= limit:
                    return transactions

            last_tx = txs[-1]
            curr_lt = last_tx.prev_trans_lt
            curr_hash = last_tx.prev_trans_hash.hex()

        return transactions[:limit]

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

        async def _con(client: LiteClient) -> None:
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

        raise BalancerError("all lite-servers failed to establish connection")

    async def close(self) -> None:
        task, self._health_task = self._health_task, None

        if task is not None and not task.done():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        tasks = [client.close() for client in self._clients]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def get_time(self) -> int:
        """
        Fetch current network time from lite-server.

        :return: Current UNIX timestamp
        """

        async def _call(provider: AdnlProvider) -> int:
            return await provider.get_time()

        return await self._with_failover(_call)

    async def get_version(self) -> int:
        """
        Fetch lite-server protocol version.

        :return: Version number
        """

        async def _call(provider: AdnlProvider) -> int:
            return await provider.get_version()

        return await self._with_failover(_call)

    async def wait_masterchain_seqno(
        self,
        seqno: int,
        timeout_ms: int,
        schema_name: str,
        data: t.Optional[dict] = None,
    ) -> dict:
        """
        Combine waitMasterchainSeqno with another lite-server query.

        :param seqno: Masterchain seqno to wait for
        :param timeout_ms: Wait timeout in milliseconds
        :param schema_name: Lite-server TL method name without prefix
        :param data: Additional method arguments
        :return: Lite-server response as dictionary
        """

        async def _call(provider: AdnlProvider) -> dict:
            return await provider.wait_masterchain_seqno(
                seqno=seqno,
                timeout_ms=timeout_ms,
                schema_name=schema_name,
                data=data,
            )

        return await self._with_failover(_call)

    async def get_masterchain_info(self) -> MasterchainInfo:
        """
        Fetch basic masterchain information.

        :return: MasterchainInfo instance
        """

        async def _call(provider: AdnlProvider) -> MasterchainInfo:
            return await provider.get_masterchain_info()

        return await self._with_failover(_call)

    async def lookup_block(
        self,
        workchain: WorkchainID,
        shard: int,
        seqno: t.Optional[int] = None,
        lt: t.Optional[int] = None,
        utime: t.Optional[int] = None,
    ) -> t.Tuple[BlockIdExt, Block]:
        """
        Locate a block by workchain/shard and one of seqno/lt/utime.

        :param workchain: Workchain identifier
        :param shard: Shard identifier
        :param seqno: Block sequence number
        :param lt: Logical time filter
        :param utime: UNIX time filter
        :return: Tuple of BlockIdExt and deserialized Block
        """

        async def _call(provider: AdnlProvider) -> t.Tuple[BlockIdExt, Block]:
            return await provider.lookup_block(
                workchain=workchain,
                shard=shard,
                seqno=seqno,
                lt=lt,
                utime=utime,
            )

        return await self._with_failover(_call)

    async def get_block_header(
        self,
        block: BlockIdExt,
    ) -> t.Tuple[BlockIdExt, Block]:
        """
        Fetch and deserialize block header by BlockIdExt.

        :param block: BlockIdExt to query
        :return: Tuple of BlockIdExt and deserialized Block
        """

        async def _call(provider: AdnlProvider) -> t.Tuple[BlockIdExt, Block]:
            return await provider.get_block_header(block)

        return await self._with_failover(_call)

    async def get_block_transactions_ext(
        self,
        block: BlockIdExt,
        count: int = 1024,
    ) -> t.List[Transaction]:
        """
        Fetch extended block transactions list.

        :param block: Target block identifier
        :param count: Maximum number of transactions per request
        :return: List of deserialized Transaction objects
        """

        async def _call(provider: AdnlProvider) -> t.List[Transaction]:
            return await provider.get_block_transactions_ext(block, count=count)

        return await self._with_failover(_call)

    async def get_all_shards_info(
        self,
        block: t.Optional[BlockIdExt] = None,
    ) -> t.List[BlockIdExt]:
        """
        Fetch shard info for all workchains at a given masterchain block.

        :param block: Masterchain block ID or None to use latest
        :return: List of shard BlockIdExt objects
        """

        async def _call(provider: AdnlProvider) -> t.List[BlockIdExt]:
            return await provider.get_all_shards_info(block)

        return await self._with_failover(_call)
