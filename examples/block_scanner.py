import time
import typing as t
from pathlib import Path

from tonutils.clients import LiteBalancer
from tonutils.tools.block_scanner import (
    BlockEvent,
    BlockScanner,
    ErrorEvent,
    TransactionsEvent,
)
from tonutils.types import NetworkGlobalID, DEFAULT_ADNL_RETRY_POLICY

# Path to the file where the last processed masterchain seqno is persisted
# Used by scanner.resume() to continue from where it left off after a restart
STORAGE_PATH = "block_scanner.mc_seqno"

# Maximum requests per second sent to lite-servers
# Reduce if you hit rate limits; increase for faster scanning on dedicated nodes
RPS_LIMIT = 100

# How far back to start scanning when using start_from(utime=...)
# 7 * 24 * 60 * 60 = 604800 seconds = 1 week ago
START_FROM_OFFSET = 7 * 24 * 60 * 60


class FileStorage:
    """File-backed storage for BlockScanner resume support.

    Persists the last processed masterchain seqno to a plain-text file.
    Pass an instance to BlockScanner(..., storage=...) to enable resume().
    """

    def __init__(self, path: t.Union[str, Path]) -> None:
        self._path = Path(path)

    async def get_mc_seqno(self) -> t.Optional[int]:
        """Read the saved seqno from file, or None if missing/invalid."""
        try:
            return int(self._path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    async def set_mc_seqno(self, seqno: int) -> None:
        """Persist the latest processed seqno to file."""
        self._path.write_text(f"{seqno}\n", encoding="utf-8")


# Initialize lite-server client from the public mainnet configuration
client = LiteBalancer.from_network_config(
    network=NetworkGlobalID.MAINNET,
    rps_limit=RPS_LIMIT,
    retry_policy=DEFAULT_ADNL_RETRY_POLICY,
)

# File-backed storage enables scanner.resume() across process restarts
storage = FileStorage(STORAGE_PATH)

# Create scanner instance bound to the client and storage
scanner = BlockScanner(client, storage=storage)


# Register handlers via decorators. All handlers receive a typed event object.
# ErrorEvent handler must never raise — exceptions inside it are silently dropped.


@scanner.on_error()
async def handle_error(event: ErrorEvent) -> None:
    """Handle internal scanner errors and failed transaction fetches.

    event.mc_block: masterchain block context where the error occurred
    event.block:    shard block context, or None for masterchain-level errors
    event.error:    the raised exception
    """
    where = f"mc_seqno={event.mc_block.seqno}"
    if event.block is not None:
        where += f", shard_seqno={event.block.seqno}"
    print(f"[error] {where}: {type(event.error).__name__}: {event.error}")


@scanner.on_block()
async def handle_block(event: BlockEvent) -> None:
    """Handle each discovered shard block.

    Emitted once per shard block before the corresponding TransactionsEvent.
    event.block:    shard block info (workchain, shard id, seqno)
    event.mc_block: parent masterchain block context (mc_seqno)
    """
    print(
        f"Block: wc={event.block.workchain}, "
        f"shard={event.block.shard:016x}, "
        f"shard_seqno={event.block.seqno}, "
        f"mc_seqno={event.mc_block.seqno}"
    )


@scanner.on_transactions()
async def handle_transactions(event: TransactionsEvent) -> None:
    """Handle transactions for a shard block.

    Emitted after handle_block for the same shard block.
    event.transactions: list of Transaction objects for this shard block
    event.block:        shard block info
    event.mc_block:     parent masterchain block context
    """
    print(
        f"Transactions: shard_seqno={event.block.seqno}, "
        f"mc_seqno={event.mc_block.seqno}, "
        f"count={len(event.transactions)}"
    )


async def main() -> None:
    # Connect to lite-servers before starting the scanner
    await client.connect()

    try:
        # Option 1: Start from the current last masterchain block
        # await scanner.start()

        # Option 2: Resume from the last saved seqno in storage
        # Requires BlockScanner(..., storage=...) and a prior run
        # await scanner.resume()

        # Option 3: Start from an explicit point in time
        # start_from() accepts exactly one of: seqno=, lt=, or utime=
        from_utime = int(time.time()) - START_FROM_OFFSET
        await scanner.start_from(utime=from_utime)
    finally:
        # Always stop the scanner and close the client on exit
        await scanner.stop()
        await client.close()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
