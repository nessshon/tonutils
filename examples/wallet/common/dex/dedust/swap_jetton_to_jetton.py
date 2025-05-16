from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2
from tonutils.wallet.messages import DedustSwapJettonToJettonMessage

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQ..."
TO_JETTON_MASTER_B_ADDRESS = "EQ..."

# Number of decimal places for the Jetton
FROM_JETTON_DECIMALS = 9
TO_JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = ToncenterV3Client()
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.transfer_message(
        message=DedustSwapJettonToJettonMessage(
            from_jetton_master_address=FROM_JETTON_MASTER_ADDRESS,
            to_jetton_master_address=TO_JETTON_MASTER_B_ADDRESS,
            jetton_amount=JETTON_AMOUNT,
            from_jetton_decimals=FROM_JETTON_DECIMALS,
            to_jetton_decimals=TO_JETTON_DECIMALS,
        ),
    )

    print("Successfully swapped Jetton to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
