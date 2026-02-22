import asyncio
import typing as t

from pytoniq_core.tl import BlockIdExt
from pytoniq_core.tlb.block import ExtBlkRef

from tonutils.clients import LiteBalancer, LiteClient
from tonutils.tools.block_scanner.events import (
    BlockEvent,
    ErrorEvent,
    TransactionsEvent,
)
from tonutils.tools.block_scanner.storage import BlockScannerStorageProtocol
from tonutils.types import MASTERCHAIN_SHARD, WorkchainID

ShardKey = t.Tuple[int, int]
SeenShardSeqno = t.Dict[ShardKey, int]
BlockQueue = asyncio.Queue[BlockIdExt]

OnError = t.Callable[[ErrorEvent], t.Awaitable[None]]
OnBlock = t.Callable[[BlockEvent], t.Awaitable[None]]
OnTransactions = t.Callable[[TransactionsEvent], t.Awaitable[None]]


class BlockScanner:
    """Asynchronous queue-based TON block scanner.

    Discovers shard blocks by following masterchain shard tips, emits
    events for each shard block, and optionally fetches transactions.
    """

    def __init__(
        self,
        client: t.Union[LiteBalancer, LiteClient],
        *,
        on_error: t.Optional[OnError] = None,
        on_block: t.Optional[OnBlock] = None,
        on_transactions: t.Optional[OnTransactions] = None,
        storage: t.Optional[BlockScannerStorageProtocol] = None,
        poll_interval: float = 0.1,
        **context: t.Any,
    ) -> None:
        """
        :param client: Lite client or balancer.
        :param on_error: Error handler callback, or `None`.
        :param on_block: Block event handler, or `None`.
        :param on_transactions: Transactions event handler, or `None`.
        :param storage: Progress storage, or `None`.
        :param poll_interval: Poll delay in seconds.
        :param context: Shared context passed to all events.
        """
        self._client = client
        self._on_error = on_error
        self._on_block = on_block
        self._on_transactions = on_transactions
        self._storage = storage
        self._poll_interval = poll_interval
        self._context = dict(context)

        self._pending_blocks: BlockQueue = asyncio.Queue()
        self._stop_event = asyncio.Event()
        self._running = False

    @staticmethod
    def _shard_key(blk: BlockIdExt) -> ShardKey:
        """Return shard key as (workchain, shard)."""
        return blk.workchain, blk.shard

    @staticmethod
    def _overflow_i64(x: int) -> int:
        """Wrap integer to signed 64-bit range."""
        return (x + 2**63) % 2**64 - 2**63

    @staticmethod
    def _lowbit64(x: int) -> int:
        """Return lowest set bit (64-bit shard math)."""
        return x & (~x + 1)

    def _child_shard(self, shard: int, *, left: bool) -> int:
        """Return left or right child shard id."""
        step = self._lowbit64(shard) >> 1
        return self._overflow_i64(shard - step if left else shard + step)

    def _parent_shard(self, shard: int) -> int:
        """Return parent shard id."""
        step = self._lowbit64(shard)
        return self._overflow_i64((shard - step) | (step << 1))

    @property
    def last_mc_block(self) -> BlockIdExt:
        """Last known masterchain block from provider cache."""
        return self._client.provider.last_mc_block

    def on_error(self, fn: t.Optional[OnError] = None) -> t.Any:
        """Decorator to set the error handler."""

        def decorator(handler: OnError) -> OnError:
            self._on_error = handler
            return handler

        return decorator if fn is None else decorator(fn)

    def on_block(self, fn: t.Optional[OnBlock] = None) -> t.Any:
        """Decorator to set the block handler."""

        def decorator(handler: OnBlock) -> OnBlock:
            self._on_block = handler
            return handler

        return decorator if fn is None else decorator(fn)

    def on_transactions(self, fn: t.Optional[OnTransactions] = None) -> t.Any:
        """Decorator to set the transactions' handler."""

        def decorator(handler: OnTransactions) -> OnTransactions:
            self._on_transactions = handler
            return handler

        return decorator if fn is None else decorator(fn)

    async def _call_error_handler(
        self,
        error: BaseException,
        mc_block: BlockIdExt,
        *,
        event: t.Any = None,
        handler: t.Any = None,
        block: t.Optional[BlockIdExt] = None,
    ) -> None:
        """Invoke the error handler with an `ErrorEvent`. Never raises."""
        if self._on_error is None:
            return

        try:
            await self._on_error(
                ErrorEvent(
                    client=self._client,
                    mc_block=mc_block,
                    context=self._context,
                    error=error,
                    event=event,
                    handler=handler,
                    block=block,
                )
            )
        except asyncio.CancelledError:
            raise
        except (BaseException,):
            return

    async def _call_handler(self, handler: t.Any, event: t.Any) -> None:
        """Call a handler, routing failures to the error handler."""
        if handler is None:
            return

        try:
            await handler(event)
        except asyncio.CancelledError:
            raise
        except BaseException as error:
            await self._call_error_handler(
                error,
                event.mc_block,
                event=event,
                handler=handler,
                block=event.block,
            )

    async def _lookup_mc_block(
        self,
        *,
        seqno: t.Optional[int] = None,
        lt: t.Optional[int] = None,
        utime: t.Optional[int] = None,
    ) -> BlockIdExt:
        """Lookup masterchain block by seqno, lt, or utime."""
        mc_block, _ = await self._client.lookup_block(
            workchain=WorkchainID.MASTERCHAIN,
            shard=MASTERCHAIN_SHARD,
            seqno=seqno,
            lt=lt,
            utime=utime,
        )
        return mc_block

    async def _wait_next_mc_block(self, mc_block: BlockIdExt) -> BlockIdExt:
        """Wait until the next masterchain block becomes available."""
        next_mc_seqno = mc_block.seqno + 1

        while not self._stop_event.is_set():
            last_mc_block = self.last_mc_block
            if next_mc_seqno <= last_mc_block.seqno:
                if next_mc_seqno == last_mc_block.seqno:
                    return last_mc_block
                return await self._lookup_mc_block(seqno=next_mc_seqno)

            await asyncio.sleep(self._poll_interval)

        return mc_block

    async def _get_seen_shard_seqno(self, mc_block: BlockIdExt) -> SeenShardSeqno:
        """Build map of last processed shard seqnos from the previous mc block."""
        seen_shard_seqno: SeenShardSeqno = {}
        if mc_block.seqno <= 0:
            return seen_shard_seqno

        prev_mc_block = await self._lookup_mc_block(seqno=mc_block.seqno - 1)
        for shard_tip in await self._client.get_all_shards_info(prev_mc_block):
            seen_shard_seqno[self._shard_key(shard_tip)] = shard_tip.seqno

        return seen_shard_seqno

    async def _process_pending_blocks(self, mc_block: BlockIdExt) -> None:
        """Process queued shard blocks and emit events."""
        while not self._stop_event.is_set():
            try:
                shard_block = self._pending_blocks.get_nowait()
            except asyncio.QueueEmpty:
                return

            block_event = BlockEvent(
                client=self._client,
                mc_block=mc_block,
                block=shard_block,
                context=self._context,
            )
            await self._call_handler(self._on_block, block_event)

            if self._on_transactions is None:
                continue

            get_block_transactions = self._client.get_block_transactions
            try:
                transactions = await get_block_transactions(shard_block)
            except asyncio.CancelledError:
                raise
            except BaseException as error:
                await self._call_error_handler(
                    error,
                    mc_block,
                    event=block_event,
                    handler=get_block_transactions,
                    block=shard_block,
                )
                transactions = []

            transactions_event = TransactionsEvent(
                client=self._client,
                mc_block=mc_block,
                block=shard_block,
                transactions=transactions,
                context=self._context,
            )
            await self._call_handler(self._on_transactions, transactions_event)

    async def _enqueue_missing_blocks(
        self,
        shard_tip: BlockIdExt,
        seen_seqno: SeenShardSeqno,
    ) -> None:
        """Enqueue unseen shard blocks in order (oldest first)."""
        shard_id = self._shard_key(shard_tip)
        if seen_seqno.get(shard_id, -1) >= shard_tip.seqno:
            return

        _, header = await self._client.get_block_header(shard_tip)
        info = header.info
        prev_ref = info.prev_ref

        if prev_ref.type_ == "prev_blk_info":
            prev: ExtBlkRef = prev_ref.prev
            prev_shard = (
                self._parent_shard(shard_tip.shard)
                if info.after_split
                else shard_tip.shard
            )

            await self._enqueue_missing_blocks(
                shard_tip=BlockIdExt(
                    workchain=shard_tip.workchain,
                    shard=prev_shard,
                    seqno=prev.seqno,
                    root_hash=prev.root_hash,
                    file_hash=prev.file_hash,
                ),
                seen_seqno=seen_seqno,
            )
        else:
            prev1, prev2 = prev_ref.prev1, prev_ref.prev2

            await self._enqueue_missing_blocks(
                shard_tip=BlockIdExt(
                    workchain=shard_tip.workchain,
                    shard=self._child_shard(shard_tip.shard, left=True),
                    seqno=prev1.seqno,
                    root_hash=prev1.root_hash,
                    file_hash=prev1.file_hash,
                ),
                seen_seqno=seen_seqno,
            )
            await self._enqueue_missing_blocks(
                shard_tip=BlockIdExt(
                    workchain=shard_tip.workchain,
                    shard=self._child_shard(shard_tip.shard, left=False),
                    seqno=prev2.seqno,
                    root_hash=prev2.root_hash,
                    file_hash=prev2.file_hash,
                ),
                seen_seqno=seen_seqno,
            )

        await self._pending_blocks.put(shard_tip)

    async def _run(self, mc_block: BlockIdExt) -> None:
        """Run scanning loop from the given masterchain block.

        :raises RuntimeError: If the scanner is already running.
        """
        if self._running:
            raise RuntimeError("BlockScanner already running")

        self._running = True
        self._stop_event.clear()

        try:
            seen_shard_seqno = await self._get_seen_shard_seqno(mc_block)

            while not self._stop_event.is_set():
                for shard_tip in await self._client.get_all_shards_info(mc_block):
                    await self._enqueue_missing_blocks(shard_tip, seen_shard_seqno)
                    seen_shard_seqno[self._shard_key(shard_tip)] = shard_tip.seqno

                await self._process_pending_blocks(mc_block)

                if self._storage is not None:
                    await self._storage.set_mc_seqno(mc_block.seqno)
                mc_block = await self._wait_next_mc_block(mc_block)
        finally:
            self._running = False
            self._stop_event.set()

    async def resume(self) -> None:
        """Resume scanning from storage.

        :raises RuntimeError: If storage is not configured or has no valid seqno.
        """
        if self._storage is None:
            raise RuntimeError("Storage is not configured")

        saved_seqno = await self._storage.get_mc_seqno()
        if saved_seqno is None or saved_seqno < 0:
            raise RuntimeError("No masterchain seqno in storage")

        last_mc_block = self.last_mc_block
        if saved_seqno > last_mc_block.seqno:
            raise RuntimeError("Storage masterchain seqno is ahead of network")

        if saved_seqno >= last_mc_block.seqno:
            mc_block = await self._wait_next_mc_block(last_mc_block)
        else:
            next_seqno = saved_seqno + 1
            mc_block = (
                last_mc_block
                if next_seqno >= last_mc_block.seqno
                else await self._lookup_mc_block(seqno=next_seqno)
            )

        await self._run(mc_block)

    async def start_from(
        self,
        *,
        seqno: t.Optional[int] = None,
        utime: t.Optional[int] = None,
        lt: t.Optional[int] = None,
    ) -> None:
        """Start scanning from an explicit masterchain point.

        Exactly one of the parameters must be provided.

        :param seqno: Masterchain seqno.
        :param utime: Unix time.
        :param lt: Logical time.
        :raises ValueError: If not exactly one parameter is provided.
        """
        provided = sum(v is not None for v in (seqno, utime, lt))
        if provided != 1:
            raise ValueError("Provide exactly one of seqno, utime, lt")

        if seqno is not None:
            mc_block = await self._lookup_mc_block(seqno=seqno)
        elif utime is not None:
            mc_block = await self._lookup_mc_block(utime=utime)
        elif lt is not None:
            mc_block = await self._lookup_mc_block(lt=lt)
        else:
            raise AssertionError("unreachable")

        await self._run(mc_block)

    async def start(self) -> None:
        """Start scanning from the current last masterchain block."""
        await self._run(self.last_mc_block)

    async def stop(self) -> None:
        """Request the scanner to stop."""
        self._stop_event.set()
