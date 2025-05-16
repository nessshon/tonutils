from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2
from tonutils.wallet.messages import StonfiSwapTONToJettonMessage

# Set to True for the test network, False for the main network
IS_TESTNET = False

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# Address of the Jetton Master for swapping (TON > USD₮)
TO_JETTON_MASTER_ADDRESS = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"  # noqa

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9

# Amount of TON to swap (in TON)
SWAP_TON_AMOUNT = 1


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.transfer_message(
        message=StonfiSwapTONToJettonMessage(
            jetton_master_address=TO_JETTON_MASTER_ADDRESS,
            ton_amount=SWAP_TON_AMOUNT,
            jetton_decimals=JETTON_DECIMALS,
        ),
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
