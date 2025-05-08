from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the subdomain manager contract
SUBDOMAIN_MANAGER_ADDRESS = "EQ..."

# The address of the next resolver contract
CONTRACT_ADDRESS = "EQ..."

# The subdomain to be registered
SUBDOMAIN = "example"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = SubdomainManager.build_set_next_resolver_record_body(SUBDOMAIN, Address(CONTRACT_ADDRESS))

    tx_hash = await wallet.transfer(
        destination=SUBDOMAIN_MANAGER_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Successfully registered subdomain and set the next resolver!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
