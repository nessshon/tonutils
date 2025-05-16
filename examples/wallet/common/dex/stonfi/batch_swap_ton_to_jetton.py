from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2
from tonutils.wallet.messages import StonfiSwapTONToJettonMessage

# Set to True for the test network, False for the main network
IS_TESTNET = False

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_transfer_messages(
        messages=[
            StonfiSwapTONToJettonMessage(
                jetton_master_address="EQ...",
                ton_amount=0.01,
                jetton_decimals=9,
            ),
            StonfiSwapTONToJettonMessage(
                jetton_master_address="EQ...",
                ton_amount=0.01,
                jetton_decimals=9,
            ),
            StonfiSwapTONToJettonMessage(
                jetton_master_address="EQ...",
                ton_amount=0.01,
                jetton_decimals=9,
            ),
            StonfiSwapTONToJettonMessage(
                jetton_master_address="EQ...",
                ton_amount=0.01,
                jetton_decimals=9,
            ),
        ],
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
