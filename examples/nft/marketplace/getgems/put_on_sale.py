from pytoniq_core import Address

from tonutils.client import ToncenterV3Client
from tonutils.nft import Collection, NFT
from tonutils.nft.marketplace.getgems.addresses import *
from tonutils.nft.marketplace.getgems.contract.salev3r3 import SaleV3R3
from tonutils.utils import to_nano
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the NFT to be listed for sale
NFT_ADDRESS = "EQ.."

# Sale price for the NFT in TON
PRICE = 1


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    nft_data = await NFT.get_nft_data(client, NFT_ADDRESS)
    royalty_params = await Collection.get_royalty_params(client, nft_data.collection_address)

    price = to_nano(PRICE)
    royalty_fee = int(price * (royalty_params.base / royalty_params.factor))
    marketplace_fee = int(price * 0.05)

    sale = SaleV3R3(
        nft_address=NFT_ADDRESS,
        owner_address=wallet.address,
        marketplace_address=TESTNET_GETGEMS_ADDRESS if IS_TESTNET else GETGEMS_ADDRESS,
        marketplace_fee_address=TESTNET_GETGEMS_FEE_ADDRESS if IS_TESTNET else GETGEMS_FEE_ADDRESS,
        royalty_address=royalty_params.address,
        marketplace_fee=marketplace_fee,
        royalty_fee=royalty_fee,
        price=price,
    )
    body = sale.build_transfer_nft_body(
        destination=Address(TESTNET_GETGEMS_DEPLOYER_ADDRESS if IS_TESTNET else GETGEMS_DEPLOYER_ADDRESS),
        owner_address=wallet.address,
        state_init=sale.state_init,
    )

    tx_hash = await wallet.transfer(
        destination=NFT_ADDRESS,
        amount=0.25,
        body=body,
    )

    # Print the result of the operation
    print(f"NFT {NFT_ADDRESS} successfully put on sale at price {PRICE} TON.")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
