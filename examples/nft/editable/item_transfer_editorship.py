from pytoniq_core import Address

from tonutils.clients import ToncenterClient
from tonutils.contracts import (
    NFTTransferEditorshipBody,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Editable NFT item address to transfer editorship
NFT_ITEM_ADDRESS = Address("EQ...")

# New editor address
EDITOR_ADDRESS = Address("UQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be current editor to transfer editorship successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Construct transfer editorship message body
    # editor_address: new editor address (receives metadata editing rights)
    # response_address: address to receive excess TON and operation confirmation
    body = NFTTransferEditorshipBody(
        editor_address=EDITOR_ADDRESS,
        response_address=wallet.address,
    )

    # Send transfer editorship transaction to Editable NFT item contract
    # destination: Editable NFT item contract address
    # body: serialized transfer editorship message
    # amount: TON attached for gas fees (0.05 TON typical)
    msg = await wallet.transfer(
        destination=NFT_ITEM_ADDRESS,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    # Display Editable NFT item address with transferred editorship
    print(f"NFT item address: {NFT_ITEM_ADDRESS.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
