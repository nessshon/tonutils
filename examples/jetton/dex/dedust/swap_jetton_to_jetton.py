from tonutils.client import TonapiClient
from tonutils.jetton import JettonMaster, JettonWallet
from tonutils.jetton.dex.dedust import Asset, Factory, PoolType, SwapStep
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQ..."
TO_JETTON_MASTER_B_ADDRESS = "EQ..."

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = TonapiClient(api_key=API_KEY)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    factory = Factory(client)
    pool_a = await factory.get_pool(
        pool_type=PoolType.VOLATILE,
        assets=[
            Asset.jetton(FROM_JETTON_MASTER_ADDRESS),
            Asset.native(),
        ],
    )
    pool_b = await factory.get_pool(
        pool_type=PoolType.VOLATILE,
        assets=[
            Asset.native(),
            Asset.jetton(TO_JETTON_MASTER_B_ADDRESS),
        ],
    )
    jetton_vault = await factory.get_jetton_vault(FROM_JETTON_MASTER_ADDRESS)
    jetton_wallet_address = await JettonMaster.get_wallet_address(
        client=client,
        owner_address=wallet.address.to_str(),
        jetton_master_address=FROM_JETTON_MASTER_ADDRESS,
    )

    tx_hash = await wallet.transfer(
        destination=jetton_wallet_address,
        amount=0.3,
        body=JettonWallet.build_transfer_body(
            recipient_address=jetton_vault.address,
            jetton_amount=int(JETTON_AMOUNT * (10 ** JETTON_DECIMALS)),
            response_address=wallet.address,
            forward_payload=jetton_vault.create_swap_payload(
                pool_address=pool_a.address,
                next_=SwapStep(pool_b.address),
            ),
            forward_amount=int(0.25 * 1e9),
        ),
    )

    print("Successfully swapped Jetton to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
