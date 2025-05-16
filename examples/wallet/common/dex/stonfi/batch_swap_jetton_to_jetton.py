from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2
from tonutils.wallet.messages import StonfiSwapJettonToJettonMessage

# Set to True for the test network, False for the main network
IS_TESTNET = False

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    client = ToncenterV3Client()
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_transfer_messages(
        messages=[
            StonfiSwapJettonToJettonMessage(
                from_jetton_master_address="EQ...",
                to_jetton_master_address="EQ...",
                jetton_amount=0.01,
                from_jetton_decimals=9,
                to_jetton_decimals=9,
            ),
            StonfiSwapJettonToJettonMessage(
                from_jetton_master_address="EQ...",
                to_jetton_master_address="EQ...",
                jetton_amount=0.01,
                from_jetton_decimals=9,
                to_jetton_decimals=9,
            ),
            StonfiSwapJettonToJettonMessage(
                from_jetton_master_address="EQ...",
                to_jetton_master_address="EQ...",
                jetton_amount=0.01,
                from_jetton_decimals=9,
                to_jetton_decimals=9,
            ),
            StonfiSwapJettonToJettonMessage(
                from_jetton_master_address="EQ...",
                to_jetton_master_address="EQ...",
                jetton_amount=0.01,
                from_jetton_decimals=9,
                to_jetton_decimals=9,
            ),
        ],
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
