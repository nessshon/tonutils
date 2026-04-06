from ton_core import (
    Address,
    JettonStandardChangeContentBody,
    NetworkGlobalID,
    OffchainContent,
    to_nano,
)

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV4R2

# Mnemonic phrase — 24 words (TON-native) or 12/18/24 words (BIP-39 import)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Deployed jetton master contract address
JETTON_MASTER_ADDRESS = Address("EQ...")

# New jetton metadata URI (TEP-64 off-chain format)
# Points to JSON with updated jetton metadata (name, symbol, decimals, image)
JETTON_MASTER_URI = "https://example.com/jetton.json"


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be current jetton admin to change content successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Configure new jetton metadata (off-chain format)
    jetton_master_content = OffchainContent(uri=JETTON_MASTER_URI)

    # Build change content message body
    # content: new metadata configuration for jetton master
    #   Updates displayed token information in wallets and explorers
    body = JettonStandardChangeContentBody(content=jetton_master_content)

    # Send change content transaction to jetton master contract
    # destination: jetton master contract address
    # amount: TON attached to message (covers gas fees, typical: 0.05 TON)
    # body: serialized change content message
    msg = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    # Display jetton master address for reference
    print(f"Jetton master address: {JETTON_MASTER_ADDRESS.to_str()}")

    # Normalized hash of the signed external message (computed locally before sending)
    # Not a blockchain transaction hash — use it to track whether the message
    # was accepted on-chain (e.g. via explorers, API queries, or your own checks)
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
