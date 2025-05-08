from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the Subdomain Collection contract
SUBDOMAIN_COLLECTION_ADDRESS = "EQ..."

# The name of the subdomain to be minted
SUBDOMAIN_NAME = "alice"  # alice → alice.ghost.ton


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_COLLECTION_ADDRESS,
        amount=0.1,
        body=SUBDOMAIN_NAME,
    )

    print(f"Successfully minted subdomain {SUBDOMAIN_NAME}!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
