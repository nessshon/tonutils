from pytoniq_core import Address

from tonutils.clients import ToncenterClient
from tonutils.contracts import (
    JettonMasterStablecoinData,
    JettonMasterStablecoinV2,
    JettonWalletStablecoinV2,
    OffchainContent,
    Vanity,
    VanityDeployBody,
    VanityResult,
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

# Vanity contract result JSON from the generator
# Clone: git clone https://github.com/ton-org/vanity
# Run: python3 src/generator.py --owner {OWNER_ADDRESS} --end {SUFFIX} --case-sensitive
# Generator results saved to: addresses.jsonl
VANITY_RESULT = '{"address":"EQ...","init":{"code":"te6cc...","fixedPrefixLength":...}'


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Get stablecoin jetton wallet code
    jetton_wallet_code = JettonWalletStablecoinV2.get_default_code()

    # Configure jetton metadata
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
    # This is the contract we want to deploy via vanity
    # Note: jetton_master.address here is NOT the final vanity address
    jetton_master = JettonMasterStablecoinV2.from_data(
        client=client,
        data=jetton_master_data.serialize(),
    )

    # Parse vanity generator output JSON
    vanity_result = VanityResult.model_validate_json(VANITY_RESULT)

    # Create vanity contract wrapper from generator result
    # Vanity contract validates owner, then replaces its code with payload
    vanity = Vanity.from_result(
        client=client,
        result=vanity_result,
    )

    # Create vanity deploy message body
    # code: jetton master initial code cell
    # data: jetton master initial data cell
    # After deployment, vanity contract becomes the actual jetton master
    body = VanityDeployBody(
        code=jetton_master.state_init.code,
        data=jetton_master.state_init.data,
    )

    # Deploy jetton master via vanity contract
    # destination: vanity contract address
    # amount: TON attached for deployment gas fees (0.05 TON typical)
    # body: contains new code and data for the contract
    # state_init: vanity contract initial state
    msg = await wallet.transfer(
        destination=vanity.address,
        amount=to_nano(0.05),
        body=body.serialize(),
        state_init=vanity.state_init,
    )

    # Display deployed jetton master address
    print(f"Jetton master address: {vanity_result.address}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
