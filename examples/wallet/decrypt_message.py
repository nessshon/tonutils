from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import WalletV4R2
from tonutils.types import NetworkGlobalID
from tonutils.utils import TextCipher

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Sender address (original message sender)
# Used for verification during decryption
SENDER_ADDRESS = Address("UQ...")

# Encrypted payload from transaction body (opcode 0x2167DA4B)
# Can be provided in multiple formats:
# - bytes: raw binary encrypted data (cipher text payload only)
# - hex string: hexadecimal encoding (cipher text payload only)
# - base64 string: base64 encoding (cipher text payload only)
# - Cell: full message body from BOC (opcode + cipher text payload)
# Extract from transaction comment field or message body
ENCRYPTED_PAYLOAD = "<encrypted payload>"


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Keep private_key for decryption as our_private_key
    wallet, _, our_private_key, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Decrypt message using end-to-end encryption (ECDH)
    # Uses elliptic curve Diffie-Hellman for shared secret derivation
    # Only recipient (with our_private_key) can decrypt message from sender
    # payload: encrypted message (bytes/hex/base64 cipher or Cell with opcode 0x2167DA4B)
    # sender_address: original sender's address (for verification)
    # our_private_key: recipient's private key for ECDH decryption
    # Sender's public key is embedded in the encrypted payload
    decrypted_comment = TextCipher.decrypt(
        payload=ENCRYPTED_PAYLOAD,
        sender_address=SENDER_ADDRESS,
        our_private_key=our_private_key,
    )

    # Display decrypted plaintext message
    print(f"Decrypted message: {decrypted_comment}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
