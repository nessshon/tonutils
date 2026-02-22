from pytoniq_core import Address

from tonutils.client import ToncenterV3Client, TonapiClient
from tonutils.jetton.dex.dedust import Factory
from tonutils.utils import to_nano, to_amount
from tonutils.wallet import WalletV4R2

# Addresses of the Jetton Masters
GASPUMP_TOKEN = 'E...'  # noqa

API_KEY = ''



async def main() -> None:
    client = ToncenterV3Client() # or TonapiClient(api_key=API_KEY)
    stack = await client.run_get_method(
        address=GASPUMP_TOKEN,
        method_name="get_full_jetton_data",
        stack=[],
    )
    total_supply = stack[0]
    mintable = stack[1]
    owner = stack[2]
    content = stack[3]
    wallet_code = stack[4]
    trade_state = stack[5]
    bonding_curve_balance = stack[6]
    commission_balance = stack[7]
    version = stack[8]
    bonding_curve_params = stack[9]
    commission_promille = stack[10]
    ton_balance = stack[11]
    price_nanotons = stack[12]
    supply_left = stack[13]
    max_supply = stack[14]

    print("Token: ", GASPUMP_TOKEN)
    print("Total Supply: ", total_supply)
    print("Mintable: ", mintable)
    print("Owner: ", owner)
    print("Content: ", content)
    print("Wallet Code: ", wallet_code)
    print("Trade State: ", trade_state)
    print("Bonding Curve Balance: ", bonding_curve_balance)
    print("Commission Balance: ", commission_balance)
    print("Version: ", version)
    print("Bonding Curve Params: ", bonding_curve_params)
    print("Commission Promille: ", commission_promille)
    print("TON Balance: ", ton_balance)
    print("Price Nanotons: ", price_nanotons)
    print("Supply Left: ", supply_left)
    print("Max Supply: ", max_supply)



if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
