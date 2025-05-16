from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the subdomain manager contract
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# The ID of the storage bag to be set for the subdomain
BAG_ID = "{hex}"

# The subdomain to be registered
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_set_storage_record_body(SUBDOMAIN, BAG_ID)

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )

    print("Subdomain successfully registered and storage record set!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
