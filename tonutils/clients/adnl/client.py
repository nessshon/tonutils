from __future__ import annotations

import typing as t

from tonutils.clients.adnl.mixin import LiteMixin
from tonutils.clients.adnl.provider import AdnlProvider
from tonutils.clients.adnl.provider.config import (
    get_mainnet_global_config,
    get_testnet_global_config,
    load_global_config,
)
from tonutils.clients.adnl.provider.models import (
    LiteServer,
    GlobalConfig,
)
from tonutils.clients.base import BaseClient
from tonutils.clients.limiter import RateLimiter
from tonutils.exceptions import NotConnectedError, ClientError
from tonutils.types import (
    BinaryLike,
    ClientType,
    NetworkGlobalID,
    RetryPolicy,
)


class LiteClient(LiteMixin, BaseClient):
    """TON blockchain client for lite-server communication over ADNL provider."""

    TYPE = ClientType.ADNL

    def __init__(
        self,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        ip: t.Union[str, int],
        port: int,
        public_key: BinaryLike,
        connect_timeout: float = 2.0,
        request_timeout: float = 10.0,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
        limiter: t.Optional[RateLimiter] = None,
    ) -> None:
        """
        Initialize lite-server client.

        To obtain lite-server connection parameters (ip, port, public_key),
        it is recommended to use a private configuration for better stability
        and performance. You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)
        Public free lite-server data may also be used, but may be unstable under load.

        :param network: Target TON network
        :param ip: Lite-server IP address or integer representation
        :param port: Lite-server port
        :param public_key: Lite-server ADNL public key
        :param connect_timeout: Timeout in seconds for connect/handshake performed
            by this client.
        :param request_timeout: Timeout in seconds for a single request executed
            by this client (one provider attempt).
        :param rps_limit: Optional requests-per-second limit for this client
        :param rps_period: Time window in seconds for RPS limit
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        :param limiter: Optional pre-configured RateLimiter (overrides rps_limit)
        """
        self.network: NetworkGlobalID = network

        if limiter is None and rps_limit is not None:
            limiter = RateLimiter(rps_limit, rps_period)

        self._provider: AdnlProvider = AdnlProvider(
            node=LiteServer(
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
    def provider(self) -> AdnlProvider:
        """
        Underlying ADNL provider.

        :return: AdnlProvider instance used for all lite-server requests
        """
        return self._provider

    @property
    def connected(self) -> bool:
        """
        Check whether the lite-server connection is established.

        :return: True if connected, False otherwise
        """
        return self._provider.connected

    @classmethod
    def from_config(
        cls,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        config: t.Union[GlobalConfig, t.Dict[str, t.Any], str],
        index: int,
        connect_timeout: float = 2.0,
        request_timeout: float = 10.0,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> LiteClient:
        """
        Create lite-server client from a configuration.

        To obtain lite-server connection parameters, it is recommended to use
        a private lite-server configuration for better stability and performance.
        You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        Public free configs may also be used, but may be unstable under load.

        :param network: Target TON network
        :param config: GlobalConfig instance, config file path as string, or raw dict
        :param index: Index of lite-server entry in the configuration
        :param connect_timeout: Timeout in seconds for connect/handshake performed
            by this client.
        :param request_timeout: Timeout in seconds for a single request executed
            by this client (one provider attempt).
        :param rps_limit: Optional requests-per-second limit for this client
        :param rps_period: Time window in seconds for RPS limit
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        :return: Configured LiteClient instance
        """
        if isinstance(config, str):
            config = load_global_config(config)
        if isinstance(config, dict):
            config = GlobalConfig(**config)

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
            public_key=ls.id,
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )

    @classmethod
    def from_network_config(
        cls,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        *,
        index: int,
        connect_timeout: float = 2.0,
        request_timeout: float = 10.0,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> LiteClient:
        """
        Create lite-server client using global network configuration fetched from ton.org.

        Public lite-servers available in the global network configuration are
        free to use but may be unstable under load. For higher reliability and
        performance, it is recommended to use private lite-server configurations,
        available from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        :param network: Target TON network
        :param index: Index of lite-server entry in the global configuration
        :param connect_timeout: Timeout in seconds for connect/handshake performed
            by this client.
        :param request_timeout: Timeout in seconds for a single request executed
            by this client (one provider attempt).
        :param rps_limit: Optional requests-per-second limit for this client
        :param rps_period: Time window in seconds for RPS limit
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        :return: Configured LiteClient instance
        """
        config_getters = {
            NetworkGlobalID.MAINNET: get_mainnet_global_config,
            NetworkGlobalID.TESTNET: get_testnet_global_config,
        }
        config = config_getters[network]()
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
        """
        Execute lite-server call using the current provider.

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

        fn = getattr(self.provider, method)
        return await fn(*args, **kwargs)
