from tonutils.client import TonapiClient
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Use True for the test network and False for the main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the NFT domain where the storage record will be set
NFT_DOMAIN_ADDRESS = "EQ..."

# The hex-encoded BAG ID for the storage record
BAG_ID = "{hex}"


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_set_storage_record_body(BAG_ID)

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.02,
        body=body,
    )

    print("Storage record set successfully!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
