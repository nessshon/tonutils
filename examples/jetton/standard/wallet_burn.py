from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    get_wallet_address_get_method,
    JettonBurnBody,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Deployed jetton master contract address
JETTON_MASTER_ADDRESS = Address("EQ...")

# Amount of jettons to burn in base units
# Multiply by 10^decimals for whole tokens (e.g., 1 * 10^9 = 1 jetton with 9 decimals)
JETTON_AMOUNT_TO_BURN = to_nano(1, decimals=9)


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must own jettons to burn successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Get jetton wallet address for the owner
    # Calls get_wallet_address() method on jetton master contract
    # Returns deterministic address derived from master + owner
    jetton_wallet_address = await get_wallet_address_get_method(
        client=client,
        address=JETTON_MASTER_ADDRESS,
        owner_address=wallet.address,
    )

    # Build burn message body
    # jetton_amount: amount of jettons to burn in base units
    # response_address: address to receive excess TON and burn confirmation
    body = JettonBurnBody(
        jetton_amount=JETTON_AMOUNT_TO_BURN,
        response_address=wallet.address,
    )

    # Send burn transaction to jetton wallet contract
    # destination: owner's jetton wallet address (not jetton master)
    # amount: TON attached to message (covers gas fees, typical: 0.05 TON)
    # body: serialized burn message
    msg = await wallet.transfer(
        destination=jetton_wallet_address,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    # Display jetton wallet address for reference
    print(f"Jetton wallet address: {jetton_wallet_address.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
