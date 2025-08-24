from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStablecoin
from tonutils.jetton.content import JettonStablecoinContent
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the Jetton Master contract
JETTON_MASTER_ADDRESS = "EQ..."

# New URI for the Jetton offchain content
# https://github.com/ton-blockchain/TEPs/blob/master/text/0064-token-data-standard.md#jetton-metadata-example-offchain
NEW_URI = "https://example.com/new-jetton.json"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    body = JettonMasterStablecoin.build_change_content_body(
        new_content=JettonStablecoinContent(NEW_URI),
    )

    tx_hash = await wallet.transfer(
        destination=JETTON_MASTER_ADDRESS,
        amount=0.05,
        body=body,
    )

    print("Successfully updated Jetton content!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
