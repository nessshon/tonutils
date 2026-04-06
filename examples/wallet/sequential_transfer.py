from ton_core import Address, NetworkGlobalID, to_nano

from tonutils.clients import ToncenterClient
from tonutils.contracts import (
    SeqnoGuard,
    TONTransferBuilder,
    WalletV4R2,
)

# Mnemonic phrase — 24 words (TON-native) or 12/18/24 words (BIP-39 import)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Destination addresses (recipients)
DESTINATION_1 = Address("UQ...")
DESTINATION_2 = Address("UQ...")
DESTINATION_3 = Address("UQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Wrap wallet in SeqnoGuard for safe sequential sends
    # Without SeqnoGuard, rapid sends can fail because the on-chain seqno
    # hasn't advanced yet — the second tx reuses the same seqno and is rejected
    # SeqnoGuard waits for on-chain seqno confirmation after each send
    # timeout: max seconds to wait for seqno to advance (default: 30.0)
    # poll_interval: delay between seqno polls in seconds (default: 1.5)
    guard = SeqnoGuard(wallet, timeout=30.0, poll_interval=1.0)

    # Send TON transfers sequentially — each confirmed before the next
    # guard.transfer() has the same signature as wallet.transfer()
    # destination: recipient address
    # amount: in nanotons (use to_nano() to convert from TON)
    # body: optional text comment (visible in explorers and recipient wallet)
    msg1 = await guard.transfer(
        destination=DESTINATION_1,
        amount=to_nano(0.01),  # Convert 0.01 TON to nanotons (10,000,000)
        body="First transfer",
    )

    # Normalized hash of the signed external message (computed locally before sending)
    # Not a blockchain transaction hash — use it to track whether the message
    # was accepted on-chain (e.g. via explorers, API queries, or your own checks)
    print(f"Transaction hash: {msg1.normalized_hash}")

    msg2 = await guard.transfer(
        destination=DESTINATION_2,
        amount=to_nano(0.02),  # Convert 0.02 TON to nanotons (20,000,000)
        body="Second transfer",
    )
    print(f"Transaction hash: {msg2.normalized_hash}")

    # guard.transfer_message() has the same signature as wallet.transfer_message()
    # Accepts any message builder: TONTransferBuilder, JettonTransferBuilder, NFTTransferBuilder
    msg3 = await guard.transfer_message(
        TONTransferBuilder(
            destination=DESTINATION_3,
            amount=to_nano(0.03),  # Convert 0.03 TON to nanotons (30,000,000)
            body="Third transfer via builder",
        )
    )
    print(f"Transaction hash: {msg3.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
