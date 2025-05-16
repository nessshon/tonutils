from tonutils.client import ToncenterV3Client
from tonutils.nft import NFTSoulbound
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the NFT to be revoked
NFT_ADDRESS = "EQ..."


async def main() -> None:
    # Initialize TonapiClient and Wallet
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = NFTSoulbound.build_revoke_body()

    tx_hash = await wallet.transfer(
        destination=NFT_ADDRESS,
        amount=0.02,
        body=body,
    )

    print(f"Successfully revoked NFT at address: {NFT_ADDRESS}.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
