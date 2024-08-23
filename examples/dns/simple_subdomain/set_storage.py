from tonutils.client import TonapiClient
from tonutils.dns.simple_subdomain import SubdomainManager
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Use True for the test network and False for the main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the subdomain manager contract
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# The ID of the storage bag to be set for the subdomain
BAG_ID = "{hex}"

# The subdomain to be registered
SUBDOMAIN = "example"


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
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
