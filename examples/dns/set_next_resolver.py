from pytoniq_core import Address

from tonutils.client import TonapiClient
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = False

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the NFT domain where the next resolver record will be set
NFT_DOMAIN_ADDRESS = "EQ..."

# The address of the contract to be set as the next resolver
CONTRACT_ADDRESS = "EQ..."


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_set_next_resolver_record_body(Address(CONTRACT_ADDRESS))

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.02,
        body=body,
    )

    print("Next resolver record set successfully!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
