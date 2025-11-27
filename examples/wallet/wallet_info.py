from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import WalletV4R2
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_amount

MNEMONIC = "word1 word2 word3 ..."

WALLET_ADDRESS = Address("UQ...")


async def main() -> None:
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    wallet = await WalletV4R2.from_address(client, WALLET_ADDRESS)

    # Or initialize from a mnemonic phrase:
    # wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Load the latest on-chain state:
    await wallet.refresh()

    ton_balance = to_amount(wallet.balance, precision=4)

    print(f"Address: {wallet.address.to_str(is_bounceable=False)}")
    print(f"State: {wallet.state.value}")
    print(f"Balance: {wallet.balance} ({ton_balance} TON)")
    print(f"Last transaction lt: {wallet.last_transaction_lt}")
    print(f"Last transaction hash: {wallet.last_transaction_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
