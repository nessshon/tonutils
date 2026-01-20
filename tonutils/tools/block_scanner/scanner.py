import asyncio
import typing as t
from dataclasses import dataclass

from pytoniq_core import Transaction
from pytoniq_core.tl import BlockIdExt

from tonutils.clients import LiteBalancer, LiteClient
from tonutils.tools.block_scanner.annotations import (
    BlockWhere,
    Decorator,
    Handler,
    TransactionWhere,
    TransactionsWhere,
)
from tonutils.tools.block_scanner.dispatcher import EventDispatcher
from tonutils.tools.block_scanner.events import (
    BlockEvent,
    TransactionEvent,
    TransactionsEvent,
)
from tonutils.tools.block_scanner.traversal import ShardTraversal
from tonutils.types import WorkchainID, MASTERCHAIN_SHARD


@dataclass(slots=True)
class _ScanState:
    """Internal scanner state per masterchain block."""

    mc_block: BlockIdExt
    shards_seqno: t.Dict[t.Tuple[int, int], int]


class BlockScanner:
    """Asynchronous scanner for TON blockchain."""

    def __init__(
        self,
        *,
        client: t.Union[LiteBalancer, LiteClient],
        poll_interval: float = 0.1,
        include_transactions: bool = True,
        max_concurrency: int = 1000,
        **context: t.Any,
    ) -> None:
        """
        Initialize a BlockScanner.

        :param client: LiteClient or LiteBalancer instance for blockchain access.
        :param poll_interval: Interval in seconds to poll for new masterchain blocks.
        :param include_transactions: If True, emit TransactionEvent and TransactionsEvent.
        :param max_concurrency: Maximum number of concurrent event handler tasks.
        :param context: Additional key/value data passed to all emitted events.
        """
        self._client = client
        self._context = dict(context)
        self._poll_interval = poll_interval
        self._include_transactions = include_transactions

        self._traversal = ShardTraversal()
        self._dispatcher = EventDispatcher(max_concurrency)

        self._stop_event = asyncio.Event()
        self._running = False

    @t.overload
    def register(
        self,
        event_type: t.Type[BlockEvent],
        handler: Handler[BlockEvent],
        *,
        where: t.Optional[BlockWhere] = None,
    ) -> None: ...

    @t.overload
    def register(
        self,
        event_type: t.Type[TransactionEvent],
        handler: Handler[TransactionEvent],
        *,
        where: t.Optional[TransactionWhere] = None,
    ) -> None: ...

    @t.overload
    def register(
        self,
        event_type: t.Type[TransactionsEvent],
        handler: Handler[TransactionsEvent],
        *,
        where: t.Optional[TransactionsWhere] = None,
    ) -> None: ...

    def register(
        self,
        event_type: t.Any,
        handler: t.Any,
        *,
        where: t.Any = None,
    ) -> None:
        """Register a handler for an event type with optional filter."""
        self._dispatcher.register(event_type, handler, where=where)

    def on_block(
        self,
        where: t.Optional[BlockWhere] = None,
    ) -> Decorator[BlockEvent]:
        """Decorator for block event handlers."""
        return self._dispatcher.on(BlockEvent, where=where)

    def on_transaction(
        self,
        where: t.Optional[TransactionWhere] = None,
    ) -> Decorator[TransactionEvent]:
        """Decorator for transaction event handlers."""
        return self._dispatcher.on(TransactionEvent, where=where)

    def on_transactions(
        self,
        where: t.Optional[TransactionsWhere] = None,
    ) -> Decorator[TransactionsEvent]:
        """Decorator for batch transaction event handlers."""
        return self._dispatcher.on(TransactionsEvent, where=where)

    def _get_last_mc_block(self) -> BlockIdExt:
        """Return last masterchain block."""
        return self._client.provider.last_mc_block

    async def _lookup_mc_block(
        self,
        seqno: t.Optional[int] = None,
        lt: t.Optional[int] = None,
        utime: t.Optional[int] = None,
    ) -> BlockIdExt:
        """Lookup masterchain block by seqno, lt, or utime."""
        mc_block, _info = await self._client.lookup_block(
            workchain=WorkchainID.MASTERCHAIN,
            shard=MASTERCHAIN_SHARD,
            seqno=seqno,
            lt=lt,
            utime=utime,
        )
        return mc_block

    async def _init_state(
        self,
        seqno: t.Optional[int] = None,
        lt: t.Optional[int] = None,
        utime: t.Optional[int] = None,
    ) -> _ScanState:
        """Initialize scanning state."""
        if seqno is None and lt is None and utime is None:
            mc_block = self._get_last_mc_block()
        else:
            mc_block = await self._lookup_mc_block(seqno=seqno, lt=lt, utime=utime)

        if mc_block.seqno > 0:
            prev_mc = await self._lookup_mc_block(seqno=mc_block.seqno - 1)
        else:
            prev_mc = mc_block

        shards_seqno: t.Dict[t.Tuple[int, int], int] = {}
        for shard in await self._client.get_all_shards_info(prev_mc):
            shards_seqno[self._traversal.shard_key(shard)] = shard.seqno

        return _ScanState(mc_block=mc_block, shards_seqno=shards_seqno)

    def _ensure_running(self) -> None:
        """Raise CancelledError if scanner was stopped."""
        if self._stop_event.is_set():
            raise asyncio.CancelledError("Block scanner stopped")

    async def _collect_blocks(
        self,
        mc_block: BlockIdExt,
        shards_seqno: t.Dict[t.Tuple[int, int], int],
    ) -> t.List[BlockIdExt]:
        """Collect all unseen shard blocks for a masterchain block."""
        shards = await self._client.get_all_shards_info(mc_block)

        blocks: t.List[BlockIdExt] = []
        for shard_tip in shards:
            blocks.extend(
                await self._traversal.walk_unseen(
                    root=shard_tip,
                    seen_seqno=shards_seqno,
                    get_header=self._client.get_block_header,
                )
            )
            # Update seen_seqno after collecting blocks for this shard
            shards_seqno[self._traversal.shard_key(shard_tip)] = shard_tip.seqno

        return blocks

    def _emit_block(self, mc_block: BlockIdExt, block: BlockIdExt) -> None:
        """Emit block event."""
        self._dispatcher.emit(
            BlockEvent(
                mc_block=mc_block,
                client=self._client,
                context=self._context,
                block=block,
            )
        )

    def _emit_transactions(
        self,
        mc_block: BlockIdExt,
        block: BlockIdExt,
        transactions: t.List[Transaction],
    ) -> None:
        """Emit batch transactions event."""
        self._dispatcher.emit(
            TransactionsEvent(
                mc_block=mc_block,
                client=self._client,
                context=self._context,
                block=block,
                transactions=transactions,
            )
        )

    def _emit_transaction(
        self,
        mc_block: BlockIdExt,
        block: BlockIdExt,
        transaction: Transaction,
    ) -> None:
        """Emit single transaction event."""
        self._dispatcher.emit(
            TransactionEvent(
                mc_block=mc_block,
                client=self._client,
                context=self._context,
                block=block,
                transaction=transaction,
            )
        )

    async def _handle_block(
        self,
        mc_block: BlockIdExt,
        block: BlockIdExt,
    ) -> None:
        """Process shard block and emit events for block + transactions."""
        self._ensure_running()
        self._emit_block(mc_block, block)

        if not self._include_transactions:
            return

        transactions = await self._client.get_block_transactions_ext(block)
        self._emit_transactions(mc_block, block, transactions)

        for transaction in transactions:
            self._ensure_running()
            self._emit_transaction(mc_block, block, transaction)

    async def _wait_next_mc_block(self, current: BlockIdExt) -> BlockIdExt:
        """Wait for next masterchain block, polling until available."""
        next_seqno = current.seqno + 1

        while True:
            self._ensure_running()
            last_mc_block = self._get_last_mc_block()

            if next_seqno <= last_mc_block.seqno:
                if next_seqno == last_mc_block.seqno:
                    return last_mc_block
                return await self._lookup_mc_block(seqno=next_seqno)

            await asyncio.sleep(self._poll_interval)

    async def start(
        self,
        from_seqno: t.Optional[int] = None,
        from_lt: t.Optional[int] = None,
        from_utime: t.Optional[int] = None,
    ) -> None:
        """
        Start scanning from the specified point.

        :param from_seqno: start from specific masterchain sequence number.
        :param from_lt: start from specific logical time (LT) of a block.
        :param from_utime: start from specific Unix timestamp.
        """
        if self._running:
            raise RuntimeError("BlockScanner is already running")

        self._running = True
        self._stop_event.clear()

        state = await self._init_state(
            seqno=from_seqno,
            lt=from_lt,
            utime=from_utime,
        )

        try:
            while not self._stop_event.is_set():
                blocks = await self._collect_blocks(
                    mc_block=state.mc_block,
                    shards_seqno=state.shards_seqno,
                )
                for block in blocks:
                    await self._handle_block(state.mc_block, block)
                state.mc_block = await self._wait_next_mc_block(state.mc_block)
        finally:
            await self._dispatcher.aclose()
            self._running = False

    async def stop(self) -> None:
        """Stop scanning."""
        self._stop_event.set()
