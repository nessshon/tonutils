from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStandard
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# The amount of Jettons to mint (in base units, considering decimals)
JETTON_AMOUNT = 1000000

# Number of decimal places for the Jetton
JETTON_DECIMALS = 9


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = JettonMasterStandard.build_mint_body(
        destination=wallet.address,
        jetton_amount=int(JETTON_AMOUNT * (10 ** JETTON_DECIMALS)),
    )

    tx_hash = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        amount=0.05,
        body=body,
    )

    print(f"Successfully minted {JETTON_AMOUNT} Jettons!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
