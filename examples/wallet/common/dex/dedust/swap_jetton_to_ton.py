from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = ToncenterV3Client()
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.dedust_swap_jetton_to_ton(
        jetton_master_address=JETTON_MASTER_ADDRESS,
        jetton_amount=JETTON_AMOUNT,
        jetton_decimals=JETTON_DECIMALS,
    )

    print("Successfully swapped Jetton to TON!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
