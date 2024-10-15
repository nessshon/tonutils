import time

from tonutils.client import TonapiClient
from tonutils.jetton.dex.dedust import Asset, AssetType, Factory, PoolType
from tonutils.jetton.dex.dedust.addresses import *
from tonutils.utils import to_nano
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for the test network, False for the main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# Amount of TON to swap
SWAP_TON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    pool_address = await Factory.get_pool_address(
        client=client,
        address=TESTNET_FACTORY_ADDRESS if IS_TESTNET else FACTORY_ADDRESS,
        pool_type=PoolType.VOLATILE,
        assets=[
            Asset.native(),
            Asset.jetton(JETTON_MASTER_ADDRESS)
        ],
    )

    body = Factory.create_swap_body(
        asset_type=AssetType.NATIVE,
        pool_address=pool_address,
        amount=to_nano(SWAP_TON_AMOUNT),
        deadline=int(time.time() + 60 * 5),
        recipient_address=wallet.address,
    )

    tx_hash = await wallet.transfer(
        destination=TESTNET_NATIVE_VAULT_ADDRESS if IS_TESTNET else NATIVE_VAULT_ADDRESS,
        amount=SWAP_TON_AMOUNT + 0.25,
        body=body,
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
