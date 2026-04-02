from __future__ import annotations

import asyncio
import typing as t

from ton_core import (
    Account,
    Address,
    Block,
    BlockIdExt,
    Cell,
    ConfigParam,
    ContractState,
    LiteServerConfig,
    ShardAccount,
    ShardStateUnsplit,
    SimpleAccount,
    Slice,
    TlGenerator,
    Transaction,
    VmStack,
    WorkchainID,
    begin_cell,
    cell_to_hex,
    check_account_proof,
    crc16,
    deserialize_shard_hashes,
    get_random,
)

from tonutils.exceptions import (
    ClientError,
    NotConnectedError,
    ProviderError,
    ProviderTimeoutError,
    RunGetMethodError,
)
from tonutils.providers.lite.pinger import PingerWorker
from tonutils.providers.lite.reader import ReaderWorker
from tonutils.providers.lite.updater import UpdaterWorker
from tonutils.transports.adnl.tcp import AdnlTcpTransport
from tonutils.transports.retry import send_with_retry
from tonutils.types import (
    DEFAULT_REQUEST_TIMEOUT,
    ContractInfo,
    MasterchainInfo,
    RetryPolicy,
)

if t.TYPE_CHECKING:
    from tonutils.transports.limiter import RateLimiter


class LiteProvider:
    """ADNL TCP provider for TON lite-servers.

    Manages a persistent encrypted connection via ``AdnlTcpTransport``,
    background ping/read/update workers, and request retry logic.
    """

    def __init__(
        self,
        node: LiteServerConfig,
        connect_timeout: float = 2.0,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
        limiter: RateLimiter | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        """Initialize the ADNL provider.

        To obtain lite-server (node) parameters (host, port, public key),
        it is recommended to use a private configuration for better stability
        and performance. You can obtain private lite-server configs from:
            - Tonconsole website: https://tonconsole.com/.
            - dTON telegram bot: https://t.me/dtontech_bot (https://dton.io/).

        :param node: Lite-server configuration (host, port, public key).
        :param connect_timeout: Timeout in seconds for connect/reconnect.
        :param request_timeout: Timeout in seconds for queries.
        :param limiter: Priority-aware rate limiter, or ``None``.
        :param retry_policy: Retry policy with per-error-code rules, or ``None``.
        """
        self.node = node
        self.connect_timeout = connect_timeout
        self.request_timeout = request_timeout
        self.transport = AdnlTcpTransport(self.node, self.connect_timeout)
        self.loop: asyncio.AbstractEventLoop | None = None

        self.tl_schemas = TlGenerator.with_default_schemas().generate()
        self.tcp_ping_tl_schema = self.tl_schemas.get_by_name("tcp.ping")
        self.ls_query_tl_schema = self.tl_schemas.get_by_name("liteServer.query")
        self.adnl_query_tl_schema = self.tl_schemas.get_by_name("adnl.message.query")

        self.pinger = PingerWorker(self)
        self.reader = ReaderWorker(self)
        self.updater = UpdaterWorker(self)

        self.pending: dict[str, asyncio.Future[t.Any]] = {}

        self._limiter: RateLimiter | None = limiter
        self._retry_policy: RetryPolicy | None = retry_policy
        self._connect_lock: asyncio.Lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        """``True`` if the underlying transport is connected."""
        return self.transport.connected

    @property
    def last_mc_block(self) -> BlockIdExt | None:
        """Last known masterchain block ID, or ``None`` if not yet fetched."""
        return self.updater.last_mc_block

    @property
    def last_ping_age(self) -> float | None:
        """Seconds since the last successful ping, or ``None``."""
        return self.pinger.last_age

    @property
    def last_ping_rtt(self) -> float | None:
        """Round-trip time of the last ping in seconds, or ``None``."""
        return self.pinger.last_rtt

    @property
    def last_ping_ms(self) -> int | None:
        """Round-trip time of the last ping in milliseconds, or ``None``."""
        if self.last_ping_rtt is None:
            return None
        return int(self.last_ping_rtt * 1000)

    async def __aenter__(self) -> LiteProvider:
        """Connect and return self."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: t.Any | None,
    ) -> None:
        """Exit async context manager and close ADNL connection."""
        await self.close()

    async def _do_connect(self) -> None:
        """Establish transport and start background workers."""
        if self.connected:
            return

        self.loop = asyncio.get_running_loop()
        await self.transport.connect()

        tasks = [self.reader.start(), self.pinger.start(), self.updater.start()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _do_close(self) -> None:
        """Stop workers, cancel pending queries, and close transport."""
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

    async def _send_once_adnl_query(self, query: bytes, *, priority: bool) -> dict[str, t.Any]:
        """Send a single ADNL query without retry.

        :param query: Encoded ADNL TL-query bytes.
        :param priority: Use priority slot in the limiter.
        :return: Decoded response dictionary.
        """
        if not self.connected or self.loop is None:
            raise NotConnectedError(
                component="LiteProvider",
                endpoint=self.node.endpoint,
                operation="request",
            )

        if self._limiter is not None:
            await self._limiter.acquire(priority=priority)

        query_id = get_random(32)
        assert self.adnl_query_tl_schema is not None
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
    ) -> dict[str, t.Any]:
        """Send a raw ADNL query with automatic retry.

        :param query: Encoded ADNL TL-query bytes.
        :param priority: Use priority slot in the limiter.
        :return: Decoded response dictionary.
        """
        return await send_with_retry(
            lambda: self._send_once_adnl_query(query, priority=priority),
            self._retry_policy,
        )

    async def send_liteserver_query(
        self,
        method: str,
        data: dict[str, t.Any] | None = None,
        *,
        priority: bool = False,
    ) -> dict[str, t.Any]:
        """Send a lite-server query by TL method name.

        :param method: Method name without ``liteServer.`` prefix.
        :param data: Method arguments.
        :param priority: Use priority slot in the limiter.
        :return: Decoded response dictionary.
        """
        if data is None:
            data = {}

        schema = self.tl_schemas.get_by_name("liteServer." + method)
        assert schema is not None
        inner = self.tl_schemas.serialize(schema, data)

        assert self.ls_query_tl_schema is not None
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
        data: dict[str, t.Any] | None = None,
        *,
        priority: bool = False,
    ) -> dict[str, t.Any]:
        """Combine waitMasterchainSeqno with another lite-server query.

        :param seqno: Masterchain seqno to wait for.
        :param timeout_ms: Wait timeout in milliseconds.
        :param schema_name: Method name without ``liteServer.`` prefix.
        :param data: Additional method arguments.
        :param priority: Use priority slot in the limiter.
        :return: Decoded response dictionary.
        """
        if data is None:
            data = {}

        wait_schema = self.tl_schemas.get_by_name("liteServer.waitMasterchainSeqno")
        assert wait_schema is not None
        wait_prefix = self.tl_schemas.serialize(
            wait_schema,
            {"seqno": seqno, "timeout_ms": timeout_ms},
        )

        suffix_schema = self.tl_schemas.get_by_name("liteServer." + schema_name)
        assert suffix_schema is not None
        suffix = self.tl_schemas.serialize(suffix_schema, data)
        assert self.ls_query_tl_schema is not None
        query = self.tl_schemas.serialize(
            self.ls_query_tl_schema,
            {"data": wait_prefix + suffix},
        )
        return await self.send_adnl_query(query, priority=priority)

    async def get_time(self, *, priority: bool = False) -> int:
        """Fetch current network time from the lite-server.

        :param priority: Use priority slot in the limiter.
        :return: Current UNIX timestamp.
        """
        result = await self.send_liteserver_query("getTime", priority=priority)
        return int(result["now"])

    async def get_version(self, *, priority: bool = False) -> int:
        """Fetch lite-server protocol version.

        :param priority: Use priority slot in the limiter.
        :return: Version number.
        """
        result = await self.send_liteserver_query("getVersion", priority=priority)
        return int(result["version"])

    async def send_message(self, body: bytes, *, priority: bool = False) -> None:
        """Send an external message to the network.

        :param body: BoC bytes of the external message.
        :param priority: Use priority slot in the limiter.
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
        """Fetch basic masterchain information.

        :param priority: Use priority slot in the limiter.
        :return: ``MasterchainInfo`` instance.
        """
        result = await self.send_liteserver_query(
            method="getMasterchainInfo",
            priority=priority,
        )
        return MasterchainInfo.from_dict(result)

    async def lookup_block(
        self,
        workchain: WorkchainID,
        shard: int,
        seqno: int | None = None,
        lt: int | None = None,
        utime: int | None = None,
        *,
        priority: bool = False,
    ) -> tuple[BlockIdExt, Block]:
        """Locate a block by workchain/shard and one of seqno, lt, or utime.

        :param workchain: Workchain identifier.
        :param shard: Shard identifier.
        :param seqno: Block sequence number.
        :param lt: Logical time filter.
        :param utime: UNIX time filter.
        :param priority: Use priority slot in the limiter.
        :return: Tuple of ``BlockIdExt`` and deserialized ``Block``.
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
    ) -> tuple[BlockIdExt, Block]:
        """Fetch and deserialize a block header.

        :param block: Block identifier to query.
        :param priority: Use priority slot in the limiter.
        :return: Tuple of ``BlockIdExt`` and deserialized ``Block``.
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

    async def get_block_transactions(
        self,
        block: BlockIdExt,
        count: int = 1024,
        *,
        priority: bool = False,
    ) -> list[Transaction]:
        """Fetch all transactions in a block.

        :param block: Target block identifier.
        :param count: Maximum transactions per request page.
        :param priority: Use priority slot in the limiter.
        :return: List of deserialized ``Transaction`` objects.
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

        transactions: list[Transaction] = []

        def _append(result_data: dict[str, t.Any]) -> None:
            """Deserialize transactions from result and append to the list."""
            if not result_data.get("transactions"):
                return
            for cell in Cell.from_boc(result_data["transactions"]):
                tx = Transaction.deserialize(cell.begin_parse())
                if isinstance(tx, Transaction):
                    transactions.append(tx)

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
        block: BlockIdExt | None = None,
        *,
        priority: bool = False,
    ) -> list[BlockIdExt]:
        """Fetch shard info for all workchains at a masterchain block.

        :param block: Masterchain block ID, or ``None`` for latest.
        :param priority: Use priority slot in the limiter.
        :return: List of shard ``BlockIdExt`` objects.
        """
        if self.last_mc_block is None:
            await self.updater.refresh()
        block = block or self.last_mc_block
        assert block is not None

        data = {"id": block.to_dict()}
        result = await self.send_liteserver_query(
            method="getAllShardsInfo",
            data=data,
            priority=priority,
        )

        cell = Cell.one_from_boc(result["data"])
        shards = deserialize_shard_hashes(cell.begin_parse())

        if shards is None:
            return []

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

    async def run_get_method(
        self,
        address: Address,
        method_name: str,
        stack: list[t.Any],
        *,
        priority: bool = False,
    ) -> list[t.Any]:
        """Execute a get-method on a contract.

        :param address: Contract address.
        :param method_name: Name of the get-method.
        :param stack: TVM stack arguments.
        :param priority: Use priority slot in the limiter.
        :return: Decoded TVM stack result.
        :raises RunGetMethodError: If the method returns a non-zero exit code.
        """
        if self.last_mc_block is None:
            await self.updater.refresh()
        assert self.last_mc_block is not None

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

    async def get_config(
        self,
        *,
        priority: bool = False,
    ) -> dict[int, t.Any]:
        """Fetch and decode full blockchain configuration.

        :param priority: Use priority slot in the limiter.
        :return: Mapping of config parameter IDs to values.
        """
        if self.last_mc_block is None:
            await self.updater.refresh()
        assert self.last_mc_block is not None

        data = {"mode": 0, "id": self.last_mc_block.to_dict()}
        result = await self.send_liteserver_query(
            method="getConfigAll",
            data=data,
            priority=priority,
        )

        config_proof = Cell.one_from_boc(result.get("config_proof"))
        return build_config_all(config_proof)

    async def get_info(
        self,
        address: Address,
        *,
        priority: bool = False,
    ) -> ContractInfo:
        """Fetch contract state at the latest masterchain block.

        :param address: Contract address.
        :param priority: Use priority slot in the limiter.
        :return: ``ContractInfo`` with balance, code, data, and last transaction.
        """
        if self.last_mc_block is None:
            await self.updater.refresh()
        assert self.last_mc_block is not None

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
            return ContractInfo(balance=0)

        account_state_root = Cell.one_from_boc(result["state"])
        account = Account.deserialize(account_state_root.begin_parse())

        shrd_blk = BlockIdExt.from_dict(result["shardblk"])
        shard_account = build_shard_account(
            account_state_root=account_state_root,
            shard_account_descr=result["proof"],
            shrd_blk=shrd_blk,
            address=address,
        )
        assert account is not None
        return build_contract_state_info(
            address=address,
            account=account,
            shard_account=shard_account,
        )

    async def get_transactions(
        self,
        account: dict[str, t.Any],
        count: int,
        from_lt: int,
        from_hash: str,
        *,
        priority: bool = False,
    ) -> list[Transaction]:
        """Fetch a chain of transactions for an account.

        :param account: TL account identifier dictionary.
        :param count: Maximum transactions to return (<= 16).
        :param from_lt: Starting logical time.
        :param from_hash: Starting transaction hash.
        :param priority: Use priority slot in the limiter.
        :return: List of ``Transaction`` objects in reverse order.
        :raises ClientError: If ``count`` exceeds 16.
        """
        if count > 16:
            raise ClientError("get_transactions supports up to 16 transactions per request")

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
        transactions: list[Transaction] = []

        for cell in cells:
            curr_hash = cell.get_hash(0).hex()
            if curr_hash != prev_tr_hash:
                raise ProviderError(
                    f"getTransactions failed: transaction hash mismatch (expected {prev_tr_hash}, got {curr_hash})"
                )

            tx_or_cell = Transaction.deserialize(cell.begin_parse())
            assert isinstance(tx_or_cell, Transaction)
            prev_tr_hash = tx_or_cell.prev_trans_hash.hex()
            transactions.append(tx_or_cell)

        return transactions

    async def get_account_state(
        self,
        address: Address,
        *,
        priority: bool = False,
    ) -> tuple[Account | None, ShardAccount | None]:
        """Fetch account state and shard account from the lite-server.

        :param address: Account address.
        :param priority: Use priority slot in the limiter.
        :return: Tuple of (``Account`` or ``None``, ``ShardAccount`` or ``None``).
        """
        if self.last_mc_block is None:
            await self.updater.refresh()
        assert self.last_mc_block is not None

        data = {
            "id": self.last_mc_block.to_dict(),
            "account": address.to_tl_account_id(),
        }
        result = await self.send_liteserver_query(
            method="getAccountState",
            data=data,
            priority=priority,
        )
        if not result.get("state"):
            return None, None

        account_state_root = Cell.one_from_boc(result["state"])
        account = Account.deserialize(account_state_root.begin_parse())

        shrd_blk = BlockIdExt.from_dict(result["shardblk"])
        shard_account = build_shard_account(
            account_state_root=account_state_root,
            shard_account_descr=result["proof"],
            shrd_blk=shrd_blk,
            address=address,
        )
        return account, shard_account


def build_config_all(config_proof: Cell) -> dict[int, t.Any]:
    """Decode full blockchain configuration from a config proof cell.

    :param config_proof: Root cell containing the config proof.
    :return: Mapping of config parameter IDs to decoded values.
    """
    shard = ShardStateUnsplit.deserialize(config_proof[0].begin_parse())
    assert shard is not None
    result: dict[int, t.Any] = {}

    assert shard.custom is not None
    for pid, cell in shard.custom.config.config.items():
        if pid in ConfigParam.params:
            result[pid] = ConfigParam.params[pid].deserialize(cell)
        else:
            result[pid] = cell
    return result


def build_shard_account(
    account_state_root: Cell,
    shard_account_descr: bytes,
    shrd_blk: BlockIdExt,
    address: Address,
) -> ShardAccount:
    """Construct a ``ShardAccount`` from proof data.

    :param account_state_root: Root cell of the account state.
    :param shard_account_descr: Proof bytes for the account descriptor.
    :param shrd_blk: Block ID the proof applies to.
    :param address: Account address being verified.
    :return: Parsed ``ShardAccount`` instance.
    """
    shard_descr = check_account_proof(
        proof=shard_account_descr,
        shrd_blk=shrd_blk,
        address=address,
        account_state_root=account_state_root,
        return_account_descr=True,
    )

    assert shard_descr is not None
    assert shard_descr.cell is not None
    full_shard_builder = begin_cell()
    full_shard_builder.store_bytes(shard_descr.cell.begin_parse().load_bytes(40))
    full_shard_builder.store_ref(account_state_root)
    full_shard_cs = full_shard_builder.to_slice()

    return ShardAccount.deserialize(full_shard_cs)


def build_contract_state_info(
    address: Address,
    account: Account,
    shard_account: ShardAccount,
) -> ContractInfo:
    """Build a ``ContractInfo`` from raw account and shard data.

    :param address: Contract address.
    :param account: Raw ``Account`` data structure.
    :param shard_account: Parsed ``ShardAccount`` entry.
    :return: Populated ``ContractInfo`` instance.
    """
    simple_account = SimpleAccount.from_raw(account, address)
    info = ContractInfo(balance=simple_account.balance)

    if simple_account.state is not None:
        state_init = simple_account.state.state_init
        if state_init is not None:
            if state_init.code is not None:
                info.code_raw = cell_to_hex(state_init.code)
            if state_init.data is not None:
                info.data_raw = cell_to_hex(state_init.data)

        info.state = ContractState(
            "uninit" if simple_account.state.type_ == "uninitialized" else simple_account.state.type_
        )

    lt = shard_account.last_trans_lt
    th = shard_account.last_trans_hash
    if lt:
        info.last_transaction_lt = int(lt)
    if th:
        info.last_transaction_hash = th.hex()

    if info.last_transaction_lt is None and info.last_transaction_hash is None and info.state == ContractState.UNINIT:
        info.state = ContractState.NONEXIST

    return info
