from tonutils.client import TonapiClient
from tonutils.jetton import JettonMaster, JettonWallet
from tonutils.jetton.dex.dedust import Asset, AssetType, Factory, PoolType, SwapStep
from tonutils.jetton.dex.dedust.addresses import *
from tonutils.utils import to_nano
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for the test network, False for the main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQ..."
TO_JETTON_MASTER_ADDRESS = "EQ..."

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    from_pool_address = await Factory.get_pool_address(
        client=client,
        address=TESTNET_FACTORY_ADDRESS if IS_TESTNET else FACTORY_ADDRESS,
        pool_type=PoolType.VOLATILE,
        assets=[
            Asset.jetton(FROM_JETTON_MASTER_ADDRESS),
            Asset.native(),
        ],
    )
    to_pool_address = await Factory.get_pool_address(
        client=client,
        address=TESTNET_FACTORY_ADDRESS if IS_TESTNET else FACTORY_ADDRESS,
        pool_type=PoolType.VOLATILE,
        assets=[
            Asset.native(),
            Asset.jetton(TO_JETTON_MASTER_ADDRESS),
        ],
    )
    jetton_vault_address = await Factory.get_vault_address(
        client=client,
        address=TESTNET_FACTORY_ADDRESS if IS_TESTNET else FACTORY_ADDRESS,
        asset=Asset.jetton(FROM_JETTON_MASTER_ADDRESS),
    )
    jetton_wallet_address = await JettonMaster.get_wallet_address(
        client=client,
        owner_address=wallet.address.to_str(),
        jetton_master_address=FROM_JETTON_MASTER_ADDRESS,
    )

    forward_payload = Factory.create_swap_body(
        asset_type=AssetType.JETTON,
        pool_address=from_pool_address,
        swap_step=SwapStep(to_pool_address),
    )
    body = JettonWallet.build_transfer_body(
        recipient_address=jetton_vault_address,
        jetton_amount=to_nano(JETTON_AMOUNT, JETTON_DECIMALS),
        response_address=wallet.address,
        forward_payload=forward_payload,
        forward_amount=to_nano(0.25),
    )

    tx_hash = await wallet.transfer(
        destination=jetton_wallet_address,
        amount=0.3,
        body=body,
    )

    print("Successfully swapped Jetton to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
