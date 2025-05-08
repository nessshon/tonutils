from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2
from tonutils.wallet.data import DedustSwapJettonToTONData

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    client = ToncenterV3Client()
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_dedust_swap_jetton_to_ton(
        data_list=[
            DedustSwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            DedustSwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            DedustSwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
            DedustSwapJettonToTONData(
                jetton_master_address="EQ...",
                jetton_amount=0.01,
                jetton_decimals=9,
            ),
        ]
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
