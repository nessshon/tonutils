"""
Block Scanner Example

Events:
- BlockEvent:
    Emitted for each discovered shard block (workchain/shard/seqno).
    event.mc_block is the current masterchain context (mc_seqno).
- TransactionsEvent:
    Emitted after BlockEvent for the same shard block if on_transactions handler
    is set. Contains the list of transactions for that shard block.
- ErrorEvent:
    Emitted on internal errors, handler failures, or transaction fetch failures.

Start modes:
- scanner.start():
    Start from the current last masterchain block (processes the current last).
- scanner.start_from(seqno=... | lt=... | utime=...):
    Start from an explicit masterchain point (exactly one argument required).
- scanner.resume():
    Resume from storage (masterchain seqno). Requires storage.

Storage:
- To use resume/persist progress between runs, you must pass a storage
  implementation (get_mc_seqno / set_mc_seqno).
- This example includes a minimal file-based storage (see FileStorage below).

Notes:
- Call client.connect() before starting the scanner.
- Use try/finally and always call scanner.stop() and client.close().
"""

import asyncio
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


class FileStorage:
    """Minimal storage for resume(): stores last masterchain seqno in a file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    async def get_mc_seqno(self) -> t.Optional[int]:
        try:
            return int(self._path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None

    async def set_mc_seqno(self, seqno: int) -> None:
        self._path.write_text(f"{seqno}\n", encoding="utf-8")


client = LiteBalancer.from_network_config(
    network=NetworkGlobalID.MAINNET,
    rps_limit=100,
    retry_policy=DEFAULT_ADNL_RETRY_POLICY,
)

storage = FileStorage("block_scanner.mc_seqno")
scanner = BlockScanner(client, storage=storage)


@scanner.on_error()
async def handle_error(event: ErrorEvent) -> None:
    """Print error context. This handler must never raise."""
    where = f"mc_seqno={event.mc_block.seqno}"
    if event.block is not None:
        where += f", shard_seqno={event.block.seqno}"
    print(f"[error] {where}: {type(event.error).__name__}: {event.error}")


@scanner.on_block()
async def handle_block(event: BlockEvent) -> None:
    """Print shard block id with masterchain context."""
    print(
        f"Block: wc={event.block.workchain}, "
        f"shard={event.block.shard:016x}, "
        f"shard_seqno={event.block.seqno}, "
        f"mc_seqno={event.mc_block.seqno}"
    )


@scanner.on_transactions()
async def handle_transactions(event: TransactionsEvent) -> None:
    """Print number of transactions for a shard block."""
    print(
        f"Transactions: shard_seqno={event.block.seqno}, "
        f"mc_seqno={event.mc_block.seqno}, "
        f"count={len(event.transactions)}"
    )


async def main() -> None:
    await client.connect()
    try:
        # Start from the current last masterchain block
        # await scanner.start()

        # Resume from storage (requires BlockScanner(..., storage=...))
        # await scanner.resume()

        # Start from explicit point: 1 week ago
        from_utime = int(time.time()) - 7 * 24 * 60 * 60
        await scanner.start_from(utime=from_utime)
    finally:
        await scanner.stop()
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
