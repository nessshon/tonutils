from pytoniq_core import Address

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV4R2, get_public_key_get_method
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano, TextCipher

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Destination address (recipient)
# Recipient must have deployed wallet contract with public key accessible via get_public_key
DESTINATION_ADDRESS = Address("UQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Keep private_key for encryption as our_private_key
    wallet, _, our_private_key, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Retrieve recipient's public key from blockchain
    # Calls get_public_key() get-method on recipient's wallet contract
    # Recipient wallet must be deployed (active state) to have accessible public key
    # Raises error if wallet is uninit or doesn't support get_public_key method
    their_public_key = await get_public_key_get_method(
        client=client,
        address=DESTINATION_ADDRESS,
    )

    # Encrypt message using end-to-end encryption
    # Uses elliptic curve Diffie-Hellman (ECDH) for shared secret
    # Only sender (with our_private_key) and recipient (with their_private_key) can decrypt
    # payload: plaintext message to encrypt
    # sender_address: included in encrypted payload for recipient verification
    # our_private_key: sender's private key for ECDH
    # their_public_key: recipient's public key for ECDH
    body = TextCipher.encrypt(
        payload="Hello from tonutils!",
        sender_address=wallet.address,
        our_private_key=our_private_key,
        their_public_key=their_public_key,
    )

    # Send TON with encrypted message
    # destination: recipient address
    # amount: in nanotons (1 TON = 1,000,000,000 nanotons)
    # body: encrypted message (only recipient can decrypt with their private key)
    msg = await wallet.transfer(
        destination=DESTINATION_ADDRESS,
        amount=to_nano(0.01),  # Convert 0.01 TON to nanotons (10,000,000)
        body=body,
    )

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
