from tonutils.client import TonapiClient
from tonutils.jetton import JettonMaster, JettonWallet
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Use True for the test network and False for the main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# The number of decimal places for the Jetton
JETTON_DECIMALS = 9

# The amount of Jettons to burn
JETTON_AMOUNT = 0.01


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    jetton_wallet_address = await JettonMaster.get_wallet_address(
        client=client,
        owner_address=wallet.address.to_str(),
        jetton_master_address=JETTON_MASTER_ADDRESS,
    )
    body = JettonWallet.build_burn_body(
        jetton_amount=int(JETTON_AMOUNT * (10 ** JETTON_DECIMALS)),
        response_address=wallet.address,
    )

    tx_hash = await wallet.transfer(
        destination=jetton_wallet_address,
        amount=0.05,  # Gas fee
        body=body,
    )

    print(f"Successfully burned {JETTON_AMOUNT} Jettons!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
