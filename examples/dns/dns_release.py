from ton_core import (
    Address,
    DNSBalanceReleaseBody,
    NetworkGlobalID,
    to_nano,
)

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV5R1

# Mnemonic phrase — 24 words (TON-native) or 12/18/24 words (BIP-39 import)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# DNS item address to release (e.g., .ton domain NFT)
# Wallet must be domain owner to release the balance
DNS_ITEM_ADDRESS = Address("EQ...")

# Minimum TON amount to attach, depends on domain character count
# (min prices from get_min_price_config in the DNS auction contract):
#   4 chars → 100 TON, 5 → 50, 6 → 40, 7 → 30, 8 → 20, 9 → 10, 10 → 5, 11+ → 1
RELEASE_AMOUNT = to_nano(5)


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be DNS item owner to release the balance successfully
    wallet, _, _, _ = WalletV5R1.from_mnemonic(client, MNEMONIC)

    # Construct DNS balance release message body
    # query_id: optional query identifier (defaults to 0)
    body = DNSBalanceReleaseBody()

    # Send balance release transaction to DNS item contract
    # destination: DNS item contract address (domain NFT)
    # amount: minimum release price for the domain length (see RELEASE_AMOUNT)
    # body: serialized balance release message
    msg = await wallet.transfer(
        destination=DNS_ITEM_ADDRESS,
        amount=RELEASE_AMOUNT,
        body=body.serialize(),
    )

    # Display DNS item address with released balance
    print(f"DNS item address: {DNS_ITEM_ADDRESS.to_str()}")

    # Normalized hash of the signed external message (computed locally before sending)
    # Not a blockchain transaction hash — use it to track whether the message
    # was accepted on-chain (e.g. via explorers, API queries, or your own checks)
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
