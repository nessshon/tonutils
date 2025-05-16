from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStablecoin, JettonWalletStablecoin
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# The amount of Jettons to burn (in base units, considering decimals)
JETTON_AMOUNT = 0.01


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    jetton_wallet_address = await JettonMasterStablecoin.get_wallet_address(
        client=client,
        owner_address=wallet.address.to_str(),
        jetton_master_address=JETTON_MASTER_ADDRESS,
    )
    body = JettonWalletStablecoin.build_burn_body(
        jetton_amount=int(JETTON_AMOUNT * (10 ** 9)),
        response_address=wallet.address,
    )

    tx_hash = await wallet.transfer(
        destination=jetton_wallet_address,
        amount=0.05,
        body=body,
    )

    print(f"Successfully burned {JETTON_AMOUNT} Jettons!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
