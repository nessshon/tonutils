from pytoniq_core import Address, begin_cell

from tonutils.client import ToncenterV3Client
from tonutils.nft import NFTStandard
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the NFT to be transferred and the new owner address
NFT_ADDRESS = "EQ..."
NEW_OWNER_ADDRESS = "UQ..."

# Optional comment to include in the forward payload
COMMENT = "Hello from tonutils!"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = NFTStandard.build_transfer_body(
        new_owner_address=Address(NEW_OWNER_ADDRESS),
        forward_payload=(
            begin_cell()
            .store_uint(0, 32)
            .store_snake_string(COMMENT)
            .end_cell()
        ),
        forward_amount=1,
    )

    tx_hash = await wallet.transfer(
        destination=NFT_ADDRESS,
        amount=0.05,
        body=body,
    )

    print(f"Successfully transferred NFT from address {NFT_ADDRESS} to new owner {NEW_OWNER_ADDRESS}.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
