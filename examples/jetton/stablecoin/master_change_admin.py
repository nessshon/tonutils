from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    JettonChangeAdminBody,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# New admin address (will control jetton minting and metadata)
ADMIN_ADDRESS = Address("UQ...")

# Deployed jetton master contract address
JETTON_MASTER_ADDRESS = Address("EQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be current jetton admin to change admin successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Build change admin message body (stablecoin-specific implementation)
    # admin_address: new admin address that will control jetton master
    #   New admin can mint tokens, change metadata, transfer admin rights
    body = JettonChangeAdminBody(admin_address=ADMIN_ADDRESS)

    # Send change admin transaction to jetton master contract
    # destination: jetton master contract address
    # amount: TON attached to message (covers gas fees, typical: 0.05 TON)
    # body: serialized change admin message
    msg = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        body=body.serialize(),
        amount=to_nano(0.05),
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
