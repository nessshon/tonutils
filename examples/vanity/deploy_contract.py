from tonutils.client import ToncenterV3Client
from tonutils.jetton import JettonMasterStandard
from tonutils.jetton.content import JettonOnchainContent
from tonutils.vanity import Vanity
from tonutils.wallet import WalletV4R2

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase
MNEMONIC = "word1 word2 word3 ..."

# The salt for the vanity address
SALT = ""


async def main() -> None:
    client = ToncenterV3Client(is_testnet=IS_TESTNET, rps=1, max_retries=1)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    jetton_master = JettonMasterStandard(
        content=JettonOnchainContent(
            name="Ness Jetton",
            symbol="NESS",
            description="Probably nothing",
            decimals=9,
            image="https://ton.org/download/ton_symbol.png",
        ),
        admin_address=wallet.address,
    )
    vanity = Vanity(
        owner_address=wallet.address,
        salt=SALT,
    )
    body = vanity.build_deploy_body(jetton_master)

    tx_hash = await wallet.transfer(
        destination=vanity.address,
        amount=0.05,
        body=body,
        state_init=vanity.state_init,
    )

    print(f"Successfully deployed contract at address: {vanity.address.to_str()}")
    print(f"Transaction hash: {tx_hash}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
