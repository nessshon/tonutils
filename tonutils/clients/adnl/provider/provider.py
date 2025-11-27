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

from tonutils.clients.adnl.provider.builder import (
    build_contract_state_info,
    build_shard_account,
    build_config_all,
)
from tonutils.clients.adnl.provider.limiter import PriorityLimiter
from tonutils.clients.adnl.provider.models import LiteServer, MasterchainInfo
from tonutils.clients.adnl.provider.transport import AdnlTcpTransport
from tonutils.clients.adnl.provider.workers import (
    PingerWorker,
    ReaderWorker,
    UpdaterWorker,
)
from tonutils.exceptions import (
    AdnlHandshakeError,
    AdnlProviderConnectError,
    AdnlServerError,
    AdnlProviderMissingBlockError,
    AdnlProviderResponseError,
    AdnlProviderClosedError,
    ClientError,
    ClientNotConnectedError,
    RateLimitExceededError,
    RunGetMethodError,
)
from tonutils.types import ContractStateInfo, WorkchainID


class AdnlProvider:

    def __init__(
        self,
        node: LiteServer,
        timeout: int = 10,
        rps_retries: t.Optional[int] = None,
        limiter: t.Optional[PriorityLimiter] = None,
    ) -> None:
        self.node = node
        self.timeout = timeout
        self.rps_retries = rps_retries
        self.transport = AdnlTcpTransport(self.node, self.timeout)
        self.loop: t.Optional[asyncio.AbstractEventLoop] = None

        self.tl_schemas = TlGenerator.with_default_schemas().generate()
        self.tcp_ping_tl_schema = self.tl_schemas.get_by_name("tcp.ping")
        self.ls_query_tl_schema = self.tl_schemas.get_by_name("liteServer.query")
        self.adnl_query_tl_schema = self.tl_schemas.get_by_name("adnl.message.query")

        self.pinger = PingerWorker(self)
        self.reader = ReaderWorker(self)
        self.updater = UpdaterWorker(self)

        self.pending: t.Dict[str, asyncio.Future] = {}

        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._limiter: t.Optional[PriorityLimiter] = limiter

    @property
    def is_connected(self) -> bool:
        return self.transport.is_connected

    @property
    def last_mc_block(self) -> BlockIdExt:
        return t.cast(BlockIdExt, self.updater.last_mc_block)

    @property
    def last_ping_age(self) -> t.Optional[float]:
        return self.pinger.last_age

    @property
    def last_ping_rtt(self) -> t.Optional[float]:
        return self.pinger.last_rtt

    @property
    def last_ping_ms(self) -> t.Optional[int]:
        if self.last_ping_rtt is None:
            return None
        return int(self.last_ping_rtt * 1000)

    async def __aenter__(self) -> AdnlProvider:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        await self.close()

    async def _do_connect(self) -> None:
        if self.is_connected:
            return

        self.loop = asyncio.get_running_loop()
        try:
            await self.transport.connect()
        except AdnlHandshakeError as exc:
            raise AdnlProviderConnectError(
                host=self.node.host,
                port=self.node.port,
                message=str(exc),
            ) from exc
        except OSError as exc:
            raise AdnlProviderConnectError(
                host=self.node.host,
                port=self.node.port,
                message=str(exc),
            ) from exc

        tasks = [self.reader.start(), self.pinger.start(), self.updater.start()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _do_close(self) -> None:
        tasks = [self.updater.stop(), self.pinger.stop(), self.reader.stop()]
        await asyncio.gather(*tasks, return_exceptions=True)

        for fut in self.pending.values():
            if not fut.done():
                fut.cancel()
        self.pending.clear()

        await self.transport.close()
        self.loop = None

    async def connect(self) -> None:
        async with self._connect_lock:
            await self._do_connect()

    async def reconnect(self) -> None:
        async with self._connect_lock:
            await self._do_close()
            await self._do_connect()

    async def close(self) -> None:
        async with self._connect_lock:
            await self._do_close()

    async def send_adnl_query(self, query: bytes, priority: bool = False) -> dict:
        if not self.is_connected or self.loop is None:
            raise ClientNotConnectedError(self)

        rps_retries = 0 if self.rps_retries is None else self.rps_retries

        for attempt in range(rps_retries + 1):
            if self._limiter is not None:
                await self._limiter.acquire(priority=priority)

            query_id = get_random(32)
            packet = self.tl_schemas.serialize(
                self.adnl_query_tl_schema,
                {
                    "query_id": query_id,
                    "query": query,
                },
            )
            query_id_key = query_id[::-1].hex()
            fut: asyncio.Future = self.loop.create_future()
            self.pending[query_id_key] = fut

            try:
                await self.transport.send_adnl_packet(packet)
                try:
                    resp = await asyncio.wait_for(fut, timeout=self.timeout)
                except asyncio.TimeoutError:
                    raise
                except asyncio.CancelledError as exc:
                    raise AdnlProviderClosedError(
                        host=self.node.host,
                        port=self.node.port,
                    ) from exc
                except AdnlServerError as e:
                    if e.code in [228, 5556]:
                        await asyncio.sleep(0.2 * (2**attempt))
                        continue
                    if e.code == 651:
                        raise AdnlProviderMissingBlockError(
                            host=self.node.host,
                            port=self.node.port,
                            message=e.message,
                        ) from e
                    raise
                if not isinstance(resp, dict):
                    raise AdnlProviderResponseError(
                        host=self.node.host,
                        port=self.node.port,
                    )
            finally:
                if query_id_key in self.pending:
                    del self.pending[query_id_key]
            return resp

        raise RateLimitExceededError(rps_retries or 1)

    async def send_liteserver_query(
        self,
        method: str,
        data: t.Optional[t.Dict[str, t.Any]] = None,
        *,
        priority: bool = False,
    ) -> t.Dict[str, t.Any]:
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
        result = await self.send_liteserver_query("getTime", priority=priority)
        return int(result["now"])

    async def get_version(self, *, priority: bool = False) -> int:
        result = await self.send_liteserver_query("getVersion", priority=priority)
        return int(result["version"])

    async def send_message(self, body: bytes, *, priority: bool = False) -> None:
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
        result = await self.send_liteserver_query(
            method="getMasterchainInfo",
            priority=priority,
        )
        return MasterchainInfo(**result)

    async def lookup_block(
        self,
        workchain: WorkchainID,
        shard: int,
        seqno: int = -1,
        lt: t.Optional[int] = None,
        utime: t.Optional[int] = None,
        *,
        priority: bool = False,
    ) -> t.Tuple[BlockIdExt, Block]:
        mode = 0
        if seqno != -1:
            mode = 1
        if lt is not None:
            mode = 2
        if utime is not None:
            mode = 4

        data = {
            "id": {
                "workchain": workchain.value,
                "shard": shard,
                "seqno": seqno,
            },
            "lt": lt,
            "mode": mode,
            "utime": utime,
        }
        result = await self.send_liteserver_query(
            method="lookupBlock",
            data=data,
            priority=priority,
        )

        cell = Cell.one_from_boc(result["header_proof"])

        return (
            BlockIdExt.from_dict(result["id"]),
            Block.deserialize(cell[0].begin_parse()),
        )

    async def get_all_shards_info(
        self,
        block: t.Optional[BlockIdExt] = None,
        *,
        priority: bool = False,
    ) -> t.List[BlockIdExt]:
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
            raise AdnlServerError(
                code=-1,
                message="RunGetMethod: missing `exit_code` in response",
            )
        if exit_code != 0:
            raise RunGetMethodError(
                address=address,
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
    ) -> list[Transaction]:
        if count > 16:
            raise ClientError(
                "`get_raw_transactions` supports up to 16 transactions per request"
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
        transactions: list[Transaction] = []

        for i, cell in enumerate(cells):
            curr_hash = cell.get_hash(0).hex()
            if curr_hash != prev_tr_hash:
                raise ClientError(
                    "Transaction hash mismatch in `raw_get_transactions`: "
                    f"expected {prev_tr_hash}, got {curr_hash}"
                )

            tx = Transaction.deserialize(cell.begin_parse())
            prev_tr_hash = tx.prev_trans_hash.hex()
            transactions.append(tx)

        return transactions
