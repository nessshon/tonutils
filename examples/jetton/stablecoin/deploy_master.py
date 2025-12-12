from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    JettonMasterStablecoinData,
    JettonMasterStablecoinV2,
    JettonTopUpBody,
    JettonWalletStablecoinV2,
    OffchainContent,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Jetton admin address (controls minting and metadata)
ADMIN_ADDRESS = Address("UQ...")

# Jetton metadata URI (TEP-64 off-chain format)
# Points to JSON with jetton metadata (name, symbol, decimals, image)
JETTON_MASTER_URI = "https://example.com/jetton.json"


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Get stablecoin jetton wallet code
    jetton_wallet_code = JettonWalletStablecoinV2.get_default_code()

    # Configure jetton metadata (off-chain format)
    jetton_master_content = OffchainContent(uri=JETTON_MASTER_URI)

    # Compose stablecoin jetton master initial data
    # admin_address: jetton admin (can mint tokens, change metadata)
    # content: jetton metadata configuration
    # jetton_wallet_code: code cell used to deploy each holder's jetton wallet
    jetton_master_data = JettonMasterStablecoinData(
        admin_address=ADMIN_ADDRESS,
        content=jetton_master_content,
        jetton_wallet_code=jetton_wallet_code,
    )

    # Create stablecoin jetton master contract instance from initial data
    # Generates master address deterministically from code + data hash
    # Address is predictable before deployment (same data = same address)
    jetton_master = JettonMasterStablecoinV2.from_data(
        client=client,
        data=jetton_master_data.serialize(),
    )

    # Create top-up message body
    # Empty body used for jetton master deployment
    body = JettonTopUpBody()

    # Deploy stablecoin jetton master contract via state_init message
    # destination: jetton master address (derived from code + data)
    # amount: TON attached for deployment gas fees (0.05 TON typical)
    # body: top-up message (funds master contract storage)
    # state_init: initial code and data for contract deployment
    msg = await wallet.transfer(
        destination=jetton_master.address,
        amount=to_nano(0.05),
        body=body.serialize(),
        state_init=jetton_master.state_init,
    )

    # Display deployed stablecoin jetton master address
    print(f"Jetton master address: {jetton_master.address.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
