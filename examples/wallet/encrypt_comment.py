from tonutils.client import TonapiClient
from tonutils.wallet import WalletV4R2

API_KEY = ""
IS_TESTNET = True

MNEMONIC = []


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
    wallet, public_key, private_key, mnemonic = WalletV4R2.from_mnemonic(MNEMONIC, client)

    destination = "UQ..."

    body = await wallet.build_encrypted_comment_body(
        text="Hello from tonutils!",
        destination=destination,
    )

    tx_hash = await wallet.transfer(
        destination=destination,
        amount=0.01,
        body=body,
    )

    print("Successfully transferred!")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
