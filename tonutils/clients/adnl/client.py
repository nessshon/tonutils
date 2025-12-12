from __future__ import annotations

import typing as t

from pytoniq_core import Address, Transaction

from tonutils.clients.adnl.provider import AdnlProvider
from tonutils.clients.adnl.provider.config import TONClient
from tonutils.clients.adnl.provider.limiter import PriorityLimiter
from tonutils.clients.adnl.provider.models import LiteServer, GlobalConfig
from tonutils.clients.adnl.stack import decode_stack, encode_stack
from tonutils.clients.base import BaseClient
from tonutils.types import BinaryLike, ClientType, ContractStateInfo, NetworkGlobalID


class AdnlClient(BaseClient):
    """TON blockchain client using ADNL lite-server as transport."""

    TYPE = ClientType.ADNL

    def __init__(
        self,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        ip: t.Union[str, int],
        port: int,
        public_key: BinaryLike,
        timeout: int = 10,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
        limiter: t.Optional[PriorityLimiter] = None,
    ) -> None:
        """
        Initialize ADNL client.

        To obtain lite-server connection parameters (ip, port, public_key),
        it is recommended to use a private configuration for better stability
        and performance. You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        Public free lite-server data may also be used via `from_network_config()`.

        :param network: Target TON network (mainnet or testnet)
        :param ip: Lite-server IP address or integer representation
        :param port: Lite-server port
        :param public_key: Lite-server ADNL public key
        :param timeout: Request timeout in seconds
        :param rps_limit: Optional requests-per-second limit
        :param rps_period: Time window in seconds for RPS limit
        :param rps_retries: Number of retries on rate limiting
        :param limiter: Optional pre-configured PriorityLimiter
        """
        self.network: NetworkGlobalID = network

        if limiter is not None:
            limiter = limiter
        elif rps_limit is not None:
            limiter = PriorityLimiter(rps_limit, rps_period)

        self._provider: AdnlProvider = AdnlProvider(
            node=LiteServer(
                ip=ip,
                port=port,
                id=public_key,
            ),
            timeout=timeout,
            rps_retries=rps_retries,
            limiter=limiter,
        )

    @property
    def provider(self) -> AdnlProvider:
        """
        Underlying ADNL provider.

        :return: AdnlProvider instance used for all ADNL requests
        """
        return self._provider

    @property
    def is_connected(self) -> bool:
        """
        Check whether ADNL transport is connected.

        :return: True if connected, False otherwise
        """
        return self._provider.is_connected

    async def __aenter__(self) -> AdnlClient:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        await self.close()

    @classmethod
    def from_config(
        cls,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        config: t.Union[GlobalConfig, t.Dict[str, t.Any]],
        index: int,
        timeout: int = 10,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
    ) -> AdnlClient:
        """
        Create ADNL client from a lite-server config.

        For best performance, it is recommended to use a private lite-server
        configuration. You can obtain private configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        Public free configs may also be used via `from_network_config()`.

        :param network: Target TON network
        :param config: GlobalConfig instance or raw dict
        :param index: Index of lite-server
        :param timeout: Request timeout in seconds
        :param rps_limit: Optional requests-per-second limit
        :param rps_period: Time window in seconds for RPS limit
        :param rps_retries: Number of retries on rate limiting
        :return: Configured AdnlClient instance
        """
        if isinstance(config, dict):
            config = GlobalConfig(**config)
        node = config.liteservers[index]
        return cls(
            network=network,
            ip=node.host,
            port=node.port,
            public_key=node.id,
            timeout=timeout,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
        )

    @classmethod
    async def from_network_config(
        cls,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        index: int,
        timeout: int = 10,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        rps_retries: int = 2,
    ) -> AdnlClient:
        """
        Create ADNL client using global network config fetched from ton.org.

        Public lite-servers available in the global network configuration are
        free to use but may be unstable under load. For higher reliability and
        performance, it is recommended to use private lite-server configurations,
        available from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        :param network: Target TON network
        :param index: Index of lite-server
        :param timeout: Request timeout in seconds
        :param rps_limit: Optional requests-per-second limit
        :param rps_period: Time window in seconds for RPS limit
        :param rps_retries: Number of retries on rate limiting
        :return: Configured AdnlClient instance
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
            index=index,
            timeout=timeout,
            rps_limit=rps_limit,
            rps_period=rps_period,
            rps_retries=rps_retries,
        )

    async def _send_boc(self, boc: str) -> None:
        return await self.provider.send_message(bytes.fromhex(boc))

    async def _get_blockchain_config(self) -> t.Dict[int, t.Any]:
        return await self.provider.get_config_all()

    async def _get_contract_info(self, address: str) -> ContractStateInfo:
        return await self.provider.get_account_state(Address(address))

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

            txs = await self.provider.get_transactions(
                account=account,
                count=batch_size,
                from_lt=curr_lt,
                from_hash=curr_hash,
            )
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
        result = await self.provider.run_smc_method(
            address=Address(address),
            method_name=method_name,
            stack=encode_stack(stack or []),
        )
        return decode_stack(result or [])

    async def connect(self) -> None:
        """Ensure that ADNL connection is established."""
        await self.provider.connect()

    async def reconnect(self) -> None:
        """Force reconnection to the lite-server."""
        await self.provider.reconnect()

    async def close(self) -> None:
        """Close ADNL connection."""
        await self.provider.close()
