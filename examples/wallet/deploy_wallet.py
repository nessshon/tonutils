from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import WalletV4R2
from tonutils.types import NetworkGlobalID

MNEMONIC = "word1 word2 word3 ..."


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Any outgoing transaction will deploy the wallet contract if needed
    msg = await wallet.transfer(destination=wallet.address, amount=0)

    print(f"Wallet address: {wallet.address.to_str(is_bounceable=False)}")
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
