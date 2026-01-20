"""
Block Scanner Example

Demonstrates real-time blockchain scanning with event-driven handlers
for blocks and transactions on the TON network.

Event types:
- BlockEvent: emitted for each new block
- TransactionEvent: emitted for each transaction individually
- TransactionsEvent: emitted once per block with all transactions

Notes:
- Always call balancer.connect() before scanner.start()
- Use try/finally for proper cleanup with scanner.stop() and balancer.close()
"""

from tonutils.clients import LiteBalancer
from tonutils.tools.block_scanner import (
    BlockScanner,
    BlockEvent,
    TransactionEvent,
    TransactionsEvent,
)
from tonutils.types import (
    NetworkGlobalID,
    DEFAULT_ADNL_RETRY_POLICY,
)

balancer = LiteBalancer.from_network_config(
    network=NetworkGlobalID.MAINNET,
    rps_limit=100,
    retry_policy=DEFAULT_ADNL_RETRY_POLICY,
)

scanner = BlockScanner(
    client=balancer,
    poll_interval=0.1,
    include_transactions=True,
)


@scanner.on_block()
async def handle_block(event: BlockEvent) -> None:
    """Handle all new blocks."""
    print(
        f"New block: workchain={event.block.workchain}, "
        f"shard={event.block.shard:016x}, "
        f"seqno={event.block.seqno}"
    )


@scanner.on_transaction()
async def handle_transaction(event: TransactionEvent) -> None:
    """Handle all transactions."""
    pass


@scanner.on_transactions()
async def handle_transactions(event: TransactionsEvent) -> None:
    """Batch handler for all transactions in a block."""
    print(f"Block {event.block.seqno}: {len(event.transactions)} transactions")


async def main() -> None:
    await balancer.connect()

    try:
        # Start from latest block
        await scanner.start()

        # Example: start from 1 week ago
        # from_utime = int(time.time()) - 7 * 24 * 60 * 60
        # await scanner.start(from_utime=from_utime)
    finally:
        await scanner.stop()
        await balancer.close()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
