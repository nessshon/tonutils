from tonutils.client import ToncenterV3Client
from tonutils.nft import Collection, NFT
from tonutils.nft.marketplace.getgems.contract.salev3r3 import SaleV3R3
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the NFT and sale contract
NFT_ADDRESS = "EQ..."
SALE_ADDRESS = "EQ..."

# New sale price for the NFT in TON
PRICE = 1


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    nft_data = await NFT.get_nft_data(client, NFT_ADDRESS)
    royalty_params = await Collection.get_royalty_params(client, nft_data.collection_address)

    price = int(PRICE * 1e9)
    royalty_fee = int(price * (royalty_params.base / royalty_params.factor))
    marketplace_fee = int(price * 0.05)

    body = SaleV3R3.build_change_price_body(
        marketplace_fee=marketplace_fee,
        royalty_fee=royalty_fee,
        price=price,
    )

    tx_hash = await wallet.transfer(
        destination=SALE_ADDRESS,
        amount=0.005,
        body=body,
    )

    print(f"Successfully updated the price for NFT sale.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
