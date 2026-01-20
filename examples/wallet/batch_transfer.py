from pytoniq_core import Address

from tonutils.clients import ToncenterClient
from tonutils.contracts import (
    TONTransferBuilder,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Send multiple transfers in a single transaction (batch transfer)
    # WalletV4 supports up to 4 messages per transaction
    # For more than 4 messages, use WalletV5*, WalletHighload* or WalletPreprocessed*
    # Can mix TONTransferBuilder, NFTTransferBuilder, and JettonTransferBuilder
    msg = await wallet.batch_transfer_message(
        [
            TONTransferBuilder(
                destination=Address("UQ..."),
                amount=to_nano(0.01),  # 0.01 TON in nanotons
                body="Hello from tonutils!",
            ),
            TONTransferBuilder(
                destination=Address("UQ..."),
                amount=to_nano(0.01),  # 0.01 TON in nanotons
                body="Hello from tonutils!",
            ),
            TONTransferBuilder(
                destination=Address("UQ..."),
                amount=to_nano(0.01),  # 0.01 TON in nanotons
                body="Hello from tonutils!",
            ),
        ]
    )

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
