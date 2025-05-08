from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStablecoin
from tonutils.jetton.content import JettonStablecoinContent
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The address of the administrator for managing the Jetton Master
ADMIN_ADDRESS = "UQ..."

# URI for the off-chain content of the Jetton
# https://github.com/ton-blockchain/TEPs/blob/master/text/0064-token-data-standard.md#jetton-metadata-example-offchain
URI = "https://example.com/jetton.json"


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    jetton_master = JettonMasterStablecoin(
        content=JettonStablecoinContent(URI),
        admin_address=ADMIN_ADDRESS,
    )

    tx_hash = await wallet.transfer(
        destination=jetton_master.address,
        amount=0.05,
        state_init=jetton_master.state_init,
    )

    print(f"Successfully deployed Jetton Master at address: {jetton_master.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
