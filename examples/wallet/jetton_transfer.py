from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    JettonTransferBuilder,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Destination address (jetton recipient)
DESTINATION_ADDRESS = Address("UQ...")

# Jetton master contract address (identifies the token type)
# Examples: USD₮, NOT, etc.
JETTON_MASTER_ADDRESS = Address("EQ...")

# Jetton amount in base units (respects token decimals)
# Example: 1 USD₮ (6 decimals) → 1 * 10^6 = 1,000,000
# Use to_nano() with decimals parameter to convert human-readable amount
JETTON_AMOUNT_TO_SEND = to_nano(1, decimals=6)


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must have jetton balance in its jetton wallet
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Transfer jettons to recipient
    # JettonTransferBuilder constructs proper jetton transfer message
    # destination: recipient address (receives jettons)
    # jetton_amount: amount in base units (respects token decimals)
    # jetton_master_address: identifies which jetton type to transfer
    # forward_payload: optional message forwarded to recipient (visible in notification)
    # forward_amount: nanotons sent to recipient (triggers transfer_notification)
    #   Must be > 0 to notify recipient (minimum 1 nanoton for TEP-74 compliance)
    # amount: TON attached to jetton wallet for gas fees (covers transfer + forward)
    #   Typical: 0.05 TON is sufficient, increase if forward_amount is higher
    msg = await wallet.transfer_message(
        JettonTransferBuilder(
            destination=DESTINATION_ADDRESS,
            jetton_amount=JETTON_AMOUNT_TO_SEND,
            jetton_master_address=JETTON_MASTER_ADDRESS,
            forward_payload="Hello from tonutils!",
            forward_amount=1,  # 1 nanoton triggers transfer_notification to recipient
            amount=to_nano(0.05),  # 0.05 TON for gas (covers jetton transfer fees)
        )
    )

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
