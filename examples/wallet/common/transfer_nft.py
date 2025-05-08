from tonutils.client import ToncenterV3Client
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
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.transfer_nft(
        destination=NEW_OWNER_ADDRESS,
        nft_address=NFT_ADDRESS,
        forward_payload=COMMENT,
    )

    print("Successfully transferred!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
