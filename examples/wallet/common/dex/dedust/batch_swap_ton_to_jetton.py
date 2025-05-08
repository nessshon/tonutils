from tonutils.client import ToncenterV3Client
from tonutils.wallet import WalletV4R2
from tonutils.wallet.data import DedustSwapTONToJettonData

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    client = ToncenterV3Client()
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    tx_hash = await wallet.batch_dedust_swap_ton_to_jetton(
        data_list=[
            DedustSwapTONToJettonData(
                jetton_master_address="EQ...",
                ton_amount=0.01,
                jetton_decimals=9,
            ),
            DedustSwapTONToJettonData(
                jetton_master_address="EQ...",
                ton_amount=0.01,
                jetton_decimals=9,
            ),
            DedustSwapTONToJettonData(
                jetton_master_address="EQ...",
                ton_amount=0.01,
                jetton_decimals=9,
            ),
            DedustSwapTONToJettonData(
                jetton_master_address="EQ...",
                ton_amount=0.01,
                jetton_decimals=9,
            ),
        ]
    )

    print("Successfully swapped TON to Jetton!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
