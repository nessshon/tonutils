from __future__ import annotations

import typing as t

from pytoniq_core import Address, BlockIdExt, Block, Transaction

from tonutils.clients.adnl.provider import AdnlProvider
from tonutils.clients.adnl.provider.config import (
    get_mainnet_global_config,
    get_testnet_global_config,
)
from tonutils.clients.adnl.provider.models import (
    LiteServer,
    GlobalConfig,
    MasterchainInfo,
)
from tonutils.clients.adnl.utils import decode_stack, encode_stack
from tonutils.clients.base import BaseClient
from tonutils.clients.limiter import RateLimiter
from tonutils.types import (
    BinaryLike,
    ClientType,
    ContractStateInfo,
    NetworkGlobalID,
    RetryPolicy,
    WorkchainID,
)


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
        connect_timeout: float = 2.0,
        request_timeout: float = 10.0,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
        limiter: t.Optional[RateLimiter] = None,
    ) -> None:
        """
        Initialize ADNL client.

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
        connect_timeout: float = 2.0,
        request_timeout: float = 10.0,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> AdnlClient:
        """
        Create ADNL client from a lite-server configuration.

        To obtain lite-server connection parameters, it is recommended to use
        a private lite-server configuration for better stability and performance.
        You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        Public free configs may also be used, but may be unstable under load.

        :param network: Target TON network
        :param config: GlobalConfig instance or raw dict
        :param index: Index of lite-server entry in the configuration
        :param connect_timeout: Timeout in seconds for connect/handshake performed
            by this client.
        :param request_timeout: Timeout in seconds for a single request executed
            by this client (one provider attempt).
        :param rps_limit: Optional requests-per-second limit for this client
        :param rps_period: Time window in seconds for RPS limit
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
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
            connect_timeout=connect_timeout,
            request_timeout=request_timeout,
            rps_limit=rps_limit,
            rps_period=rps_period,
            retry_policy=retry_policy,
        )

    @classmethod
    def from_network_config(
        cls,
        *,
        network: NetworkGlobalID = NetworkGlobalID.MAINNET,
        index: int,
        connect_timeout: float = 2.0,
        request_timeout: float = 10.0,
        rps_limit: t.Optional[int] = None,
        rps_period: float = 1.0,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> AdnlClient:
        """
        Create ADNL client using global network configuration fetched from ton.org.

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
        :return: Configured AdnlClient instance
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
        transactions: t.List[Transaction] = []

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
                trimmed: t.List[Transaction] = []
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

    async def get_time(self) -> int:
        """
        Fetch current network time from lite-server.

        :return: Current UNIX timestamp
        """
        return await self.provider.get_time()

    async def get_version(self) -> int:
        """
        Fetch lite-server protocol version.

        :return: Version number
        """
        return await self.provider.get_version()

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
        return await self.provider.wait_masterchain_seqno(
            seqno=seqno,
            timeout_ms=timeout_ms,
            schema_name=schema_name,
            data=data,
        )

    async def get_masterchain_info(self) -> MasterchainInfo:
        """
        Fetch basic masterchain information.

        :return: MasterchainInfo instance
        """
        return await self.provider.get_masterchain_info()

    async def lookup_block(
        self,
        workchain: WorkchainID,
        shard: int,
        seqno: int = -1,
        lt: t.Optional[int] = None,
        utime: t.Optional[int] = None,
    ) -> t.Tuple[BlockIdExt, Block]:
        """
        Locate a block by workchain/shard and one of seqno/lt/utime.

        :param workchain: Workchain identifier
        :param shard: Shard identifier
        :param seqno: Block seqno or -1 to ignore
        :param lt: Logical time filter
        :param utime: UNIX time filter
        :return: Tuple of BlockIdExt and deserialized Block
        """
        return await self.provider.lookup_block(
            workchain=workchain,
            shard=shard,
            seqno=seqno,
            lt=lt,
            utime=utime,
        )

    async def get_block_header(
        self,
        block: BlockIdExt,
    ) -> t.Tuple[BlockIdExt, Block]:
        """
        Fetch and deserialize block header by BlockIdExt.

        :param block: BlockIdExt to query
        :return: Tuple of BlockIdExt and deserialized Block
        """
        return await self.provider.get_block_header(block)

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
        return await self.provider.get_block_transactions_ext(block, count=count)

    async def get_all_shards_info(
        self,
        block: t.Optional[BlockIdExt] = None,
    ) -> t.List[BlockIdExt]:
        """
        Fetch shard info for all workchains at a given masterchain block.

        :param block: Masterchain block ID or None to use latest
        :return: List of shard BlockIdExt objects
        """
        return await self.provider.get_all_shards_info(block)
