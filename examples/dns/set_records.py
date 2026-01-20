from pytoniq_core import Address

from tonutils.clients import ToncenterClient
from tonutils.contracts import (
    ChangeDNSRecordBody,
    DNSRecordWallet,
    WalletV4R2,
)
from tonutils.types import DNSCategory, NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# DNS item address to update (e.g., .ton domain NFT)
# Wallet must be domain owner to change DNS records
DNS_ITEM_ADDRESS = Address("EQ...")

# Wallet address to set as DNS record value
# This address will be linked to the domain
WALLET_ADDRESS = Address("UQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be DNS item owner to change records successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # DNS categories and their record types with accepted value types:
    #   DNSCategory.DNS_NEXT_RESOLVER → DNSRecordDNSNextResolver (accepts: `Address`)
    #   DNSCategory.STORAGE           → DNSRecordStorage         (accepts: `BagID`)
    #   DNSCategory.WALLET            → DNSRecordWallet          (accepts: `Address`)
    #   DNSCategory.SITE              → DNSRecordSite            (accepts: `ADNL`)

    # Construct change DNS record message body
    # category: DNS record category to update
    # record: DNS record value (wallet address for WALLET category)
    body = ChangeDNSRecordBody(
        category=DNSCategory.WALLET,
        record=DNSRecordWallet(WALLET_ADDRESS),
    )

    # Send change DNS record transaction to DNS item contract
    # destination: DNS item contract address (domain NFT)
    # amount: TON attached for gas fees (0.05 TON typical)
    # body: serialized change DNS record message
    msg = await wallet.transfer(
        destination=DNS_ITEM_ADDRESS,
        amount=to_nano(0.05),
        body=body.serialize(),
    )

    # Display DNS item address with updated record
    print(f"DNS item address: {DNS_ITEM_ADDRESS.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
