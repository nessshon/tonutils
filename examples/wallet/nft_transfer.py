from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import NFTTransferBuilder, WalletV4R2
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# NFT item address (specific NFT token)
NFT_ITEM_ADDRESS = Address("EQ...")

# Destination address (new NFT owner)
DESTINATION_ADDRESS = Address("UQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be the current owner of the NFT
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Transfer NFT to new owner
    # NFTTransferBuilder constructs proper NFT transfer message
    # destination: new owner address
    # nft_address: specific NFT item contract address
    # forward_payload: optional message forwarded to new owner (visible in notification)
    # forward_amount: nanotons sent to new owner (triggers ownership_assigned notification)
    #   Must be > 0 to notify recipient (minimum 1 nanoton for TEP-62 compliance)
    # amount: TON attached to NFT item for gas fees (covers transfer + forward)
    #   Typical: 0.05 TON is sufficient, increase if forward_amount is higher
    msg = await wallet.transfer_message(
        NFTTransferBuilder(
            destination=DESTINATION_ADDRESS,
            nft_address=NFT_ITEM_ADDRESS,
            forward_payload="Hello from tonutils!",
            forward_amount=1,  # 1 nanoton triggers ownership_assigned notification to recipient
            amount=to_nano(0.05),  # 0.05 TON for gas (covers NFT transfer fees)
        )
    )

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
