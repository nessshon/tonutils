"""
Block Scanner Example

Demonstrates real-time blockchain scanning with event-driven handlers
for blocks and transactions on the TON network.

Event types:
- BlockEvent: emitted for each new block
- TransactionEvent: emitted for each transaction individually
- TransactionsEvent: emitted once per block with all transactions

Built-in filters:
- sender(*addresses): match by sender address(es)
- destination(*addresses): match by destination address(es)
- opcode(*ops): match by operation code(s)
- comment(*texts): match by text comment(s)

Filter composition:
- filter_a & filter_b: AND
- filter_a | filter_b: OR
- ~filter_a: NOT

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
    sender,
    destination,
    opcode,
    comment,
)
from tonutils.types import (
    NetworkGlobalID,
    DEFAULT_ADNL_RETRY_POLICY,
)
from tonutils.utils import normalize_hash

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


@scanner.on_transaction(sender("UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0"))
async def handle_from_address(event: TransactionEvent) -> None:
    """Filter by sender address."""
    tx_hash = normalize_hash(event.transaction.in_msg)
    print(f"From monitored address:", tx_hash)


@scanner.on_transaction(destination("UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0"))
async def handle_to_address(event: TransactionEvent) -> None:
    """Filter by destination address."""
    tx_hash = normalize_hash(event.transaction.in_msg)
    print("To monitored address:", tx_hash)


@scanner.on_transaction(comment("test"))
async def handle_test_comment(event: TransactionEvent) -> None:
    """Filter by text comment."""
    tx_hash = normalize_hash(event.transaction.in_msg)
    print("Test comment received:", tx_hash)


@scanner.on_transaction(opcode(0x5FCC3D14))
async def handle_nft_transfer(event: TransactionEvent) -> None:
    """Filter by opcode (NFT Transfer)."""
    tx_hash = normalize_hash(event.transaction.in_msg)
    print("NFT Transfer detected:", tx_hash)


@scanner.on_transactions()
async def handle_batch_transactions(event: TransactionsEvent) -> None:
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
