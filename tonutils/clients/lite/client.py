from __future__ import annotations

import typing as t

from ton_core import (
    BinaryLike,
    GlobalConfig,
    LiteServerConfig,
    NetworkGlobalID,
    get_mainnet_global_config,
    get_testnet_global_config,
)

from tonutils.clients.base import BaseClient
from tonutils.clients.config import resolve_config
from tonutils.clients.lite.mixin import LiteMixin
from tonutils.exceptions import (
    ClientError,
    NetworkNotSupportedError,
    NotConnectedError,
)
from tonutils.providers.lite import LiteProvider
from tonutils.transports.limiter import RateLimiter
from tonutils.types import (
    DEFAULT_REQUEST_TIMEOUT,
    ClientType,
    RetryPolicy,
)


class LiteClient(LiteMixin, BaseClient):
    """Single lite-server client over ADNL TCP.

    For multiserver balancing with automatic failover, use ``LiteBalancer``.
    """

    TYPE = ClientType.ADNL

    def __init__(
        self,
        network: NetworkGlobalID,
        *,
        ip: str | int,
        port: int,
        public_key: BinaryLike,
        connect_timeout: float = 2.0,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
        rps_limit: int | None = None,
        rps_period: float = 1.0,
        retry_policy: RetryPolicy | None = None,
        limiter: RateLimiter | None = None,
    ) -> None:
        """Initialize the lite client.

        To obtain lite-server connection parameters (ip, port, public_key),
        it is recommended to use a private configuration for better stability
        and performance. You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/.
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/).
        Public free lite-server data may also be used, but may be unstable under load.

        :param network: Target TON network.
        :param ip: Lite-server IP address or integer representation.
        :param port: Lite-server port.
        :param public_key: Lite-server ADNL public key.
        :param connect_timeout: Timeout in seconds for connect/handshake.
        :param request_timeout: Timeout in seconds for a single request.
        :param rps_limit: Requests-per-second limit, or ``None``.
        :param rps_period: Time window in seconds for RPS limit.
        :param retry_policy: Retry policy with per-error-code rules, or ``None``.
        :param limiter: Pre-configured ``RateLimiter`` (overrides ``rps_limit``), or ``None``.
        """
        self.network: NetworkGlobalID = network

        if limiter is None and rps_limit is not None:
            limiter = RateLimiter(rps_limit, rps_period)

        self._provider: LiteProvider = LiteProvider(
            node=LiteServerConfig(
                ip=ip,
                port=port,
                id=public_key,
            ),
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
            limiter=limiter,
            retry_policy=retry_policy,
        )

    @property
    def provider(self) -> LiteProvider:
        """Underlying ADNL provider."""
        return self._provider

    @property
    def connected(self) -> bool:
        """``True`` if the lite-server connection is established."""
        return self._provider.connected

    @classmethod
    def from_config(
        cls,
        network: NetworkGlobalID,
        *,
        config: GlobalConfig | dict[str, t.Any] | str,
        index: int,
        connect_timeout: float = 2.0,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
        rps_limit: int | None = None,
        rps_period: float = 1.0,
        retry_policy: RetryPolicy | None = None,
    ) -> LiteClient:
        """Create a ``LiteClient`` from a configuration.

        To obtain lite-server connection parameters, it is recommended to use
        a private lite-server configuration for better stability and performance.
        You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/.
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/).

        :param network: Target TON network.
        :param config: ``GlobalConfig``, file path, or raw dict.
        :param index: Lite-server index in the configuration.
        :param connect_timeout: Timeout in seconds for connect/handshake.
        :param request_timeout: Timeout in seconds for a single request.
        :param rps_limit: Requests-per-second limit, or ``None``.
        :param rps_period: Time window in seconds for RPS limit.
        :param retry_policy: Retry policy with per-error-code rules, or ``None``.
        :return: Configured ``LiteClient`` instance.
        :raises ClientError: If ``index`` is out of range.
        """
        config = resolve_config(config)

        liteservers = config.liteservers
        if not 0 <= index < len(liteservers):
            raise ClientError(
                f"{cls.__name__}.from_config: "
                f"liteserver index {index} is out of range "
                f"(available: 0..{len(liteservers) - 1})."
            )
        ls = config.liteservers[index]

        return cls(
            network=network,
            ip=ls.host,
            port=ls.port,
            public_key=ls.pub_key,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )

    @classmethod
    def from_network_config(
        cls,
        network: NetworkGlobalID,
        *,
        index: int,
        connect_timeout: float = 2.0,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
        rps_limit: int | None = None,
        rps_period: float = 1.0,
        retry_policy: RetryPolicy | None = None,
    ) -> LiteClient:
        """Create a ``LiteClient`` using global config fetched from ton.org.

        Public lite-servers available in the global network configuration are
        free to use but may be unstable under load. For higher reliability and
        performance, it is recommended to use private lite-server configurations,
        available from:
            - Tonconsole website: https://tonconsole.com/.
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/).

        :param network: Target TON network.
        :param index: Lite-server index in the global configuration.
        :param connect_timeout: Timeout in seconds for connect/handshake.
        :param request_timeout: Timeout in seconds for a single request.
        :param rps_limit: Requests-per-second limit, or ``None``.
        :param rps_period: Time window in seconds for RPS limit.
        :param retry_policy: Retry policy with per-error-code rules, or ``None``.
        :return: Configured ``LiteClient`` instance.
        """
        config_getters = {
            NetworkGlobalID.MAINNET: get_mainnet_global_config,
            NetworkGlobalID.TESTNET: get_testnet_global_config,
        }
        getter = config_getters.get(network)
        if getter is None:
            raise NetworkNotSupportedError(network, provider="LiteClient")
        config = getter()
        return cls.from_config(
            network=network,
            config=config,
            index=index,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )

    async def connect(self) -> None:
        """Establish connection to the lite-server."""
        await self.provider.connect()

    async def close(self) -> None:
        """Close the lite-server connection."""
        await self.provider.close()

    async def _adnl_call(self, method: str, /, *args: t.Any, **kwargs: t.Any) -> t.Any:
        """Execute a provider call, raising if not connected.

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

        fn = getattr(self.provider, method)
        return await fn(*args, **kwargs)
