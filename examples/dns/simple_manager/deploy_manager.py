from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.dns import DNS
from tonutils.dns.subdomain_manager import SubdomainManager
from tonutils.wallet import WalletV4R2
from tonutils.wallet.messages import TransferMessage

# Set to True for test network, False for main network
IS_TESTNET = False

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the administrator for managing the Subdomain Manager
ADMIN_ADDRESS = "UQ..."

# NFT domain address from TON DNS Domains
# Obtainable from https://dns.ton.org/ or https://dns.ton.org/?testnet=true
DOMAIN_ADDRESS = "EQ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    subdomain_manager = SubdomainManager(Address(ADMIN_ADDRESS))

    tx_hash = await wallet.batch_transfer_messages(
        [
            # Deploy collection
            TransferMessage(
                destination=subdomain_manager.address,
                amount=0.05,
                state_init=subdomain_manager.state_init,
            ),
            # Binding a Subdomain Manager to the main domain
            TransferMessage(
                destination=DOMAIN_ADDRESS,
                amount=0.05,
                body=DNS.build_set_next_resolver_record_body(subdomain_manager.address),
            ),
        ]
    )

    print(f"Successfully deployed Subdomain Manager at address: {subdomain_manager.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
