from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import WalletV4R2
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_amount

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Address of the wallet you want to inspect
WALLET_ADDRESS = Address("UQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Initialize wallet from existing address (read-only mode)
    # Use this when you only need to query wallet state without signing
    wallet = await WalletV4R2.from_address(client, WALLET_ADDRESS)

    # Alternative: Initialize from mnemonic (full access mode)
    # Use this when you need to send transactions and sign messages
    # wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Fetch latest on-chain state from blockchain
    # Updates: balance, state, last_transaction_lt, last_transaction_hash
    # Call this before reading wallet properties to ensure fresh data
    await wallet.refresh()

    # Convert balance from nanotons to TON with 4 decimal precision
    # 1 TON = 1,000,000,000 nanotons (10^9)
    ton_balance = to_amount(wallet.balance, precision=4)

    # Display wallet information
    print(f"Address: {wallet.address.to_str(is_bounceable=False)}")

    # State: uninit (not deployed), active (deployed), frozen (suspended)
    print(f"State: {wallet.state.value}")

    # Balance in nanotons and human-readable TON format
    print(f"Balance: {wallet.balance} ({ton_balance} TON)")

    # Logical time of last transaction (used for transaction ordering)
    print(f"Last transaction lt: {wallet.last_transaction_lt}")

    # Hash of last transaction (for tracking on explorers)
    print(f"Last transaction hash: {wallet.last_transaction_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
