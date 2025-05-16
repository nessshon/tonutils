from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2
from tonutils.wallet.messages import StonfiSwapJettonToJettonMessage

# Set to True for the test network, False for the main network
IS_TESTNET = False

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Addresses of the Jetton Masters for swapping
FROM_JETTON_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"  # noqa
TO_JETTON_MASTER_ADDRESS = "EQAvlWFDxGF2lXm67y4yzC17wYKD9A0guwPkMs1gOsM__NOT"  # noqa

# Number of decimal places for the Jetton
FROM_JETTON_DECIMALS = 6
TO_JETTON_DECIMALS = 9

# Amount of Jettons to swap (in base units, considering decimals)
JETTON_AMOUNT = 1


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.transfer_message(
        message=StonfiSwapJettonToJettonMessage(
            from_jetton_master_address=FROM_JETTON_MASTER_ADDRESS,
            to_jetton_master_address=TO_JETTON_MASTER_ADDRESS,
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
