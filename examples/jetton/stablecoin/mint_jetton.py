from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    JettonInternalTransferBody,
    JettonMintBody,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Recipient address (receives minted jettons)
# Address of the user's regular wallet (not jetton wallet)
DESTINATION_ADDRESS = Address("UQ...")

# Deployed jetton master contract address
JETTON_MASTER_ADDRESS = Address("EQ...")

# Amount of jettons to mint in base units
# Multiply by 10^decimals for whole tokens (e.g., 1 * 10^9 = 1 jetton with 9 decimals)
JETTON_AMOUNT_TO_MINT = to_nano(1, decimals=9)


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be jetton admin to mint successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Build internal transfer message
    # Sent from jetton master to recipient's jetton wallet
    # jetton_amount: amount of jettons to mint in base units
    # response_address: address to receive excess TON and confirmation
    # forward_amount: nanotons forwarded to recipient (1 nanoton triggers transfer_notification)
    internal_transfer = JettonInternalTransferBody(
        jetton_amount=JETTON_AMOUNT_TO_MINT,
        response_address=wallet.address,
        forward_amount=1,
    )

    # Construct mint message body (stablecoin-specific implementation)
    # destination: recipient's regular wallet address
    # forward_amount: TON attached to deploy/fund recipient's jetton wallet (0.1 TON typical)
    # internal_transfer: embedded message with mint details
    body = JettonMintBody(
        internal_transfer=internal_transfer,
        destination=DESTINATION_ADDRESS,
        forward_amount=to_nano(0.1),
    )

    # Send mint transaction to jetton master contract
    # destination: jetton master contract address
    # amount: TON attached to message (covers gas + forward_amount)
    #   Must be >= forward_amount + gas fees (typical: 0.125 TON total)
    # body: serialized mint message
    msg = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        amount=to_nano(0.125),
        body=body.serialize(),
    )

    # Display jetton master address for reference
    print(f"Jetton master address: {JETTON_MASTER_ADDRESS.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
