import time

from tonutils.client import TonapiClient
from tonutils.jetton.dex.dedust import Asset, Factory, PoolType, SwapParams, VaultNative
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# Amount of TON to swap (in TON)
SWAP_TON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    pool = await Factory(client).get_pool(
        pool_type=PoolType.VOLATILE,
        assets=[
            Asset.native(),
            Asset.jetton(JETTON_MASTER_ADDRESS)
        ],
    )
    swap_params = SwapParams(
        deadline=int(time.time() + 60 * 5),
        recipient_address=wallet.address,
    )

    tx_hash = await wallet.transfer(
        destination=VaultNative.ADDRESS,
        amount=SWAP_TON_AMOUNT + 0.25,
        body=VaultNative.create_swap_payload(
            amount=int(SWAP_TON_AMOUNT * 1e9),
            pool_address=pool.address,
            swap_params=swap_params
        ),
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
