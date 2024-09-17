from tonutils.client import TonapiClient
from tonutils.dns.contract import Domain
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the NFT domain where the site record will be set
NFT_DOMAIN_ADDRESS = "EQ..."

# The ADNL address that will be set in the DNS record
ADNL_ADDRESS = "{hex}"


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = Domain.build_set_site_record_body(ADNL_ADDRESS)

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.02,
        body=body,
    )

    print("Site record set successfully!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
