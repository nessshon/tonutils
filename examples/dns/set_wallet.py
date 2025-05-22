from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.dns.contract import DNS
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = False

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the NFT domain where the wallet record will be set
NFT_DOMAIN_ADDRESS = "EQ..."

# The address of the wallet that will be set in the DNS record
WALLET_ADDRESS = "UQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = DNS.build_set_wallet_record_body(Address(WALLET_ADDRESS))

    tx_hash = await wallet.transfer(
        destination=NFT_DOMAIN_ADDRESS,
        amount=0.02,
        body=body,
    )

    print("Wallet record set successfully!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
