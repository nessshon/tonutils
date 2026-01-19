from __future__ import annotations

import asyncio
import typing as t

from pytoniq_core import (
    Account,
    Address,
    Block,
    BlockIdExt,
    Cell,
    Slice,
    TlGenerator,
    Transaction,
    VmStack,
    deserialize_shard_hashes,
)
from pytoniq_core.crypto.ciphers import get_random
from pytoniq_core.crypto.crc import crc16

from tonutils.clients.adnl.provider.models import LiteServer, MasterchainInfo
from tonutils.clients.adnl.provider.transport import AdnlTcpTransport
from tonutils.clients.adnl.provider.workers import (
    PingerWorker,
    ReaderWorker,
    UpdaterWorker,
)
from tonutils.clients.adnl.utils import (
    build_contract_state_info,
    build_shard_account,
    build_config_all,
)
from tonutils.clients.limiter import RateLimiter
from tonutils.exceptions import (
    ClientError,
    NotConnectedError,
    ProviderError,
    RunGetMethodError,
    ProviderTimeoutError,
    RetryLimitError,
    ProviderResponseError,
)
from tonutils.types import (
    ContractStateInfo,
    RetryPolicy,
    WorkchainID,
)


class AdnlProvider:
    """ADNL-based provider for TON lite-servers."""

    def __init__(
        self,
        node: LiteServer,
        connect_timeout: float = 2.0,
        request_timeout: float = 10.0,
        limiter: t.Optional[RateLimiter] = None,
        retry_policy: t.Optional[RetryPolicy] = None,
    ) -> None:
        """
        Initialize ADNL provider for a specific lite-server.

        To obtain lite-server (node) parameters (host, port, public key),
        it is recommended to use a private configuration for better stability
        and performance. You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/)

        :param node: LiteServer configuration (host, port, public key)
        :param connect_timeout: Timeout in seconds for connect/reconnect
        :param request_timeout: Timeout in seconds for queries
        :param limiter: Optional priority-aware rate limiter
        :param retry_policy: Optional retry policy that defines per-error-code retry rules
        """
        self.node = node
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        self.transport = AdnlTcpTransport(self.node, self.connect_timeout)
        self.loop: t.Optional[asyncio.AbstractEventLoop] = None

        self.tl_schemas = TlGenerator.with_default_schemas().generate()
        self.tcp_ping_tl_schema = self.tl_schemas.get_by_name("tcp.ping")
        self.ls_query_tl_schema = self.tl_schemas.get_by_name("liteServer.query")
        self.adnl_query_tl_schema = self.tl_schemas.get_by_name("adnl.message.query")

        self.pinger = PingerWorker(self)
        self.reader = ReaderWorker(self)
        self.updater = UpdaterWorker(self)

        self.pending: t.Dict[str, asyncio.Future] = {}

        self._limiter: t.Optional[RateLimiter] = limiter
        self._retry_policy: t.Optional[RetryPolicy] = retry_policy
        self._connect_lock: asyncio.Lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """
        Whether the underlying transport is currently connected.

        :return: True if connected, False otherwise
        """
        return self.transport.is_connected

    @property
    def last_mc_block(self) -> BlockIdExt:
        """
        Last known masterchain block ID.

        :return: BlockIdExt of the latest masterchain block
        """
        return t.cast(BlockIdExt, self.updater.last_mc_block)

    @property
    def last_ping_age(self) -> t.Optional[float]:
        """
        Age of the last successful ping in seconds.

        :return: Seconds since last ping or None if unknown
        """
        return self.pinger.last_age

    @property
    def last_ping_rtt(self) -> t.Optional[float]:
        """
        Round-trip time of the last ping in seconds.

        :return: Ping RTT in seconds or None if unknown
        """
        return self.pinger.last_rtt

    @property
    def last_ping_ms(self) -> t.Optional[int]:
        """
        Round-trip time of the last successful ping.

        :return: Ping RTT in milliseconds, or None if unknown
        """
        if self.last_ping_rtt is None:
            return None
        return int(self.last_ping_rtt * 1000)

    async def __aenter__(self) -> AdnlProvider:
        """
        Enter async context manager and open ADNL connection.

        :return: Self instance with active transport and workers
        """
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        """Exit async context manager and close ADNL connection."""
        await self.close()

    async def _do_connect(self) -> None:
        """
        Internal connect routine.

        Establishes transport, performs handshake and starts background workers.
        """
        if self.is_connected:
            return

        self.loop = asyncio.get_running_loop()
        await self.transport.connect()

        tasks = [self.reader.start(), self.pinger.start(), self.updater.start()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _do_close(self) -> None:
        """
        Internal close routine.

        Stops background workers, cancels pending queries and closes transport.
        """
        tasks = [self.updater.stop(), self.pinger.stop(), self.reader.stop()]
        await asyncio.gather(*tasks, return_exceptions=True)

        for fut in self.pending.values():
            if not fut.done():
                fut.cancel()
        self.pending.clear()

        await self.transport.close()
        self.loop = None

    async def connect(self) -> None:
        """Connect to the lite-server if not already connected."""
        async with self._connect_lock:
            await self._do_connect()

    async def reconnect(self) -> None:
        """Force reconnection to the lite-server."""
        async with self._connect_lock:
            await self._do_close()
            await self._do_connect()

    async def close(self) -> None:
        """Close the lite-server connection and stop workers."""
        async with self._connect_lock:
            await self._do_close()

    async def _send_once_adnl_query(self, query: bytes, *, priority: bool) -> dict:
        """
        Send a single ADNL query.

        :param query: Encoded ADNL TL-query bytes
        :param priority: Whether to use priority slot in the limiter
        :return: Lite-server response payload as a decoded dictionary
        """
        if not self.is_connected or self.loop is None:
            raise NotConnectedError()

        if self._limiter is not None:
            await self._limiter.acquire(priority=priority)

        query_id = get_random(32)
        packet = self.tl_schemas.serialize(
            self.adnl_query_tl_schema,
            {"query_id": query_id, "query": query},
        )

        query_id_key = query_id[::-1].hex()
        fut: asyncio.Future[t.Any] = self.loop.create_future()
        self.pending[query_id_key] = fut

        try:
            await self.transport.send_adnl_packet(packet)

            try:
                resp = await asyncio.wait_for(fut, timeout=self.request_timeout)
            except asyncio.TimeoutError as exc:
                raise ProviderTimeoutError(
                    timeout=self.request_timeout,
                    endpoint=self.node.endpoint,
                    operation="request",
                ) from exc

            if not isinstance(resp, dict):
                raise ProviderError(f"invalid response type: {type(resp).__name__}")
            return resp

        finally:
            if query_id_key in self.pending:
                del self.pending[query_id_key]

    async def send_adnl_query(
        self,
        query: bytes,
        priority: bool = False,
    ) -> dict:
        """
        Send a raw ADNL query with retry handling based on retry policy.

        On server error, retries the request according to the rule associated
        with the received error code. If no rule matches, or retry attempts are
        exhausted, the error is raised.

        :param query: Encoded ADNL TL-query bytes
        :param priority: Whether to use priority slot in the limiter
        :return: Lite-server response payload as a decoded dictionary
        """
        attempts: t.Dict[int, int] = {}

        while True:
            try:
                return await self._send_once_adnl_query(query, priority=priority)

            except ProviderResponseError as e:
                policy = self._retry_policy
                if policy is None:
                    raise

                rule = policy.rule_for(e.code, e.message)
                if rule is None:
                    raise

                key = id(rule)
                n = attempts.get(key, 0) + 1
                attempts[key] = n

                if n >= rule.attempts:
                    raise RetryLimitError(
                        attempts=n,
                        max_attempts=rule.attempts,
                        last_error=e,
                    ) from e

                await asyncio.sleep(rule.delay(n - 1))

    async def send_liteserver_query(
        self,
        method: str,
        data: t.Optional[t.Dict[str, t.Any]] = None,
        *,
        priority: bool = False,
    ) -> t.Dict[str, t.Any]:
        """
        Send a lite-server query by TL method name.

        :param method: liteServer.<method> name without prefix
        :param data: Arguments for the method as a dict
        :param priority: Whether to use priority slot in the limiter
        :return: Lite-server response as dictionary
        """
        if data is None:
            data = {}

        schema = self.tl_schemas.get_by_name("liteServer." + method)
        inner = self.tl_schemas.serialize(schema, data)

        query = self.tl_schemas.serialize(
            self.ls_query_tl_schema,
            {"data": inner},
        )
        return await self.send_adnl_query(query, priority=priority)

    async def wait_masterchain_seqno(
        self,
        seqno: int,
        timeout_ms: int,
        schema_name: str,
        data: t.Optional[dict] = None,
        *,
        priority: bool = False,
    ) -> dict:
        """
        Combine waitMasterchainSeqno with another lite-server query.

        :param seqno: Masterchain seqno to wait for
        :param timeout_ms: Wait timeout in milliseconds
        :param schema_name: Lite-server TL method name without prefix
        :param data: Additional method arguments
        :param priority: Whether to use priority slot in the limiter
        :return: Lite-server response as dictionary
        """
        if data is None:
            data = {}

        wait_schema = self.tl_schemas.get_by_name("liteServer.waitMasterchainSeqno")
        wait_prefix = self.tl_schemas.serialize(
            wait_schema,
            {"seqno": seqno, "timeout_ms": timeout_ms},
        )

        suffix_schema = self.tl_schemas.get_by_name("liteServer." + schema_name)
        suffix = self.tl_schemas.serialize(suffix_schema, data)
        query = self.tl_schemas.serialize(
            self.ls_query_tl_schema,
            {"data": wait_prefix + suffix},
        )
        return await self.send_adnl_query(query, priority=priority)

    async def get_time(self, *, priority: bool = False) -> int:
        """
        Fetch current network time from lite-server.

        :param priority: Whether to use priority slot in the limiter
        :return: Current UNIX timestamp
        """
        result = await self.send_liteserver_query("getTime", priority=priority)
        return int(result["now"])

    async def get_version(self, *, priority: bool = False) -> int:
        """
        Fetch lite-server protocol version.

        :param priority: Whether to use priority slot in the limiter
        :return: Version number
        """
        result = await self.send_liteserver_query("getVersion", priority=priority)
        return int(result["version"])

    async def send_message(self, body: bytes, *, priority: bool = False) -> None:
        """
        Send an external message to the network.

        :param body: BoC bytes of the external message
        :param priority: Whether to use priority slot in the limiter
        :return: None
        """
        data = {"body": body}
        await self.send_liteserver_query(
            method="sendMessage",
            data=data,
            priority=priority,
        )

    async def get_masterchain_info(
        self,
        *,
        priority: bool = False,
    ) -> MasterchainInfo:
        """
        Fetch basic masterchain information.

        :param priority: Whether to use priority slot in the limiter
        :return: MasterchainInfo instance
        """
        result = await self.send_liteserver_query(
            method="getMasterchainInfo",
            priority=priority,
        )
        return MasterchainInfo(**result)

    async def lookup_block(
        self,
        workchain: WorkchainID,
        shard: int,
        seqno: t.Optional[int] = None,
        lt: t.Optional[int] = None,
        utime: t.Optional[int] = None,
        *,
        priority: bool = False,
    ) -> t.Tuple[BlockIdExt, Block]:
        """
        Locate a block by workchain/shard and one of seqno/lt/utime.

        :param workchain: Workchain identifier
        :param shard: Shard identifier
        :param seqno: Block sequence number
        :param lt: Logical time filter
        :param utime: UNIX time filter
        :param priority: Whether to use priority slot in the limiter
        :return: Tuple of BlockIdExt and deserialized Block
        """
        mode = 0
        block_seqno = 0

        if seqno is not None:
            mode = 1
            block_seqno = seqno
        if lt is not None:
            mode = 2
        if utime is not None:
            mode = 4

        data = {
            "mode": mode,
            "id": {
                "workchain": workchain,
                "shard": shard,
                "seqno": block_seqno,
            },
            "lt": lt,
            "utime": utime,
        }

        result = await self.send_liteserver_query(
            "lookupBlock",
            data=data,
            priority=priority,
        )

        block_id = BlockIdExt.from_dict(result["id"])
        header_proof = Cell.one_from_boc(result["header_proof"])
        block = Block.deserialize(header_proof[0].begin_parse())

        return block_id, block

    async def get_block_header(
        self,
        block: BlockIdExt,
        *,
        priority: bool = False,
    ) -> t.Tuple[BlockIdExt, Block]:
        """
        Fetch and deserialize block header by BlockIdExt.

        :param block: BlockIdExt to query
        :param priority: Whether to use priority slot in the limiter
        :return: Tuple of BlockIdExt and deserialized Block
        """
        data = {"id": block.to_dict(), "mode": 0}

        result = await self.send_liteserver_query(
            "getBlockHeader",
            data=data,
            priority=priority,
        )

        block_id = BlockIdExt.from_dict(result["id"])
        header_proof = Cell.one_from_boc(result["header_proof"])
        block_obj = Block.deserialize(header_proof[0].begin_parse())

        return block_id, block_obj

    async def get_block_transactions_ext(
        self,
        block: BlockIdExt,
        count: int = 1024,
        *,
        priority: bool = False,
    ) -> t.List[Transaction]:
        """
        Fetch extended block transactions list.

        :param block: Target block identifier
        :param count: Maximum number of transactions per request
        :param priority: Whether to use priority slot in the limiter
        :return: List of deserialized Transaction objects
        """
        mode = 39
        result = await self.send_liteserver_query(
            method="listBlockTransactionsExt",
            data={
                "id": block.to_dict(),
                "mode": mode,
                "count": count,
                "want_proof": b"",
            },
            priority=priority,
        )

        transactions: t.List[Transaction] = []

        def _append(result_data: dict) -> None:
            if not result_data.get("transactions"):
                return
            for cell in Cell.from_boc(result_data["transactions"]):
                transactions.append(Transaction.deserialize(cell.begin_parse()))

        _append(result)

        while result.get("incomplete"):
            mode = 167
            after = {
                "account": transactions[-1].account_addr_hex,
                "lt": transactions[-1].lt,
            }

            result = await self.send_liteserver_query(
                method="listBlockTransactionsExt",
                data={
                    "id": block.to_dict(),
                    "mode": mode,
                    "count": count,
                    "want_proof": b"",
                    "after": after,
                },
                priority=priority,
            )

            _append(result)

        return transactions

    async def get_all_shards_info(
        self,
        block: t.Optional[BlockIdExt] = None,
        *,
        priority: bool = False,
    ) -> t.List[BlockIdExt]:
        """
        Fetch shard info for all workchains at a given masterchain block.

        :param block: Masterchain block ID or None to use latest
        :param priority: Whether to use priority slot in the limiter
        :return: List of shard BlockIdExt objects
        """
        if self.last_mc_block is None:
            await self.updater.refresh()
        block = block or self.last_mc_block

        data = {"id": block.to_dict()}
        result = await self.send_liteserver_query(
            method="getAllShardsInfo",
            data=data,
            priority=priority,
        )

        cell = Cell.one_from_boc(result["data"])
        shards = deserialize_shard_hashes(cell.begin_parse())

        return [
            BlockIdExt(
                workchain=wc,
                shard=sh.next_validator_shard_signed,
                seqno=sh.seq_no,
                root_hash=sh.root_hash,
                file_hash=sh.file_hash,
            )
            for wc, v in shards.items()
            for sh in v.list
        ]

    async def run_smc_method(
        self,
        address: Address,
        method_name: str,
        stack: t.List[t.Any],
        *,
        priority: bool = False,
    ) -> t.List[t.Any]:
        """
        Execute a get-method on a contract using lite-server.

        :param address: Contract address
        :param method_name: Name of the method to run
        :param stack: TVM stack arguments
        :param priority: Whether to use priority slot in the limiter
        :return: Decoded TVM stack items returned by the method
        """
        if self.last_mc_block is None:
            await self.updater.refresh()

        crc_id = int.from_bytes(crc16(method_name.encode()), byteorder="big")
        method_id = (crc_id & 0xFFFF) | 0x10000
        params = VmStack.serialize(stack).to_boc()
        account = address.to_tl_account_id()

        data = {
            "id": self.last_mc_block.to_dict(),
            "mode": 7,
            "account": account,
            "method_id": method_id,
            "params": params,
        }
        result = await self.send_liteserver_query(
            method="runSmcMethod",
            data=data,
            priority=priority,
        )

        exit_code = result.get("exit_code")
        if exit_code is None:
            raise ProviderError("runSmcMethod: missing exit_code in response")

        if exit_code != 0:
            raise RunGetMethodError(
                address=address.to_str(),
                method_name=method_name,
                exit_code=exit_code,
            )

        cs = Slice.one_from_boc(result["result"])
        return VmStack.deserialize(cs)

    async def get_config_all(
        self,
        *,
        priority: bool = False,
    ) -> t.Dict[int, t.Any]:
        """
        Fetch and decode full blockchain configuration.

        :param priority: Whether to use priority slot in the limiter
        :return: Mapping of config parameter IDs to values
        """
        if self.last_mc_block is None:
            await self.updater.refresh()

        data = {"mode": 0, "id": self.last_mc_block.to_dict()}
        result = await self.send_liteserver_query(
            method="getConfigAll",
            data=data,
            priority=priority,
        )

        config_proof = Cell.one_from_boc(result.get("config_proof"))
        return build_config_all(config_proof)

    async def get_account_state(
        self,
        address: Address,
        *,
        priority: bool = False,
    ) -> ContractStateInfo:
        """
        Fetch contract state at the latest masterchain block.

        :param address: Contract address
        :param priority: Whether to use priority slot in the limiter
        :return: ContractStateInfo with balance, code, data and last tx
        """
        if self.last_mc_block is None:
            await self.updater.refresh()

        data = {
            "id": self.last_mc_block.to_dict(),
            "account": address.to_tl_account_id(),
        }
        result = await self.send_liteserver_query(
            method="getAccountState",
            data=data,
            priority=priority,
        )
        if not result["state"]:
            return ContractStateInfo(balance=0)

        account_state_root = Cell.one_from_boc(result["state"])
        account = Account.deserialize(account_state_root.begin_parse())

        shrd_blk = BlockIdExt.from_dict(result["shardblk"])
        shard_account = build_shard_account(
            account_state_root=account_state_root,
            shard_account_descr=result["proof"],
            shrd_blk=shrd_blk,
            address=address,
        )
        return build_contract_state_info(
            address=address,
            account=account,
            shard_account=shard_account,
        )

    async def get_transactions(
        self,
        account: dict,
        count: int,
        from_lt: int,
        from_hash: str,
        *,
        priority: bool = False,
    ) -> t.List[Transaction]:
        """
        Fetch a chain of transactions for an account.

        :param account: TL account identifier dictionary
        :param count: Maximum number of transactions to return (<= 16)
        :param from_lt: Start logical time
        :param from_hash: Start transaction hash
        :param priority: Whether to use priority slot in the limiter
        :return: List of Transaction objects in reverse order
        """
        if count > 16:
            raise ClientError(
                "get_transactions supports up to 16 transactions per request"
            )

        data = {
            "count": count,
            "account": account,
            "lt": from_lt,
            "hash": from_hash,
        }

        result = await self.send_liteserver_query(
            "getTransactions",
            data=data,
            priority=priority,
        )
        cells = Cell.from_boc(result["transactions"])

        prev_tr_hash = from_hash
        transactions: t.List[Transaction] = []

        for i, cell in enumerate(cells):
            curr_hash = cell.get_hash(0).hex()
            if curr_hash != prev_tr_hash:
                raise ClientError(
                    f"transaction hash mismatch: "
                    f"expected {prev_tr_hash}, got {curr_hash}"
                )

            tx = Transaction.deserialize(cell.begin_parse())
            prev_tr_hash = tx.prev_trans_hash.hex()
            transactions.append(tx)

        return transactions
