"""
Step 1: Clone the repository
git clone https://github.com/ton-community/vanity-contract

Step 2: Install the required dependencies
pip install -r requirements.txt

Step 3: Run the Vanity Address Generator Script
python src/generator/run.py --end {suffix} -w -0 --case-sensitive {owner_address}
- Replace {suffix} with the desired ending for the generated address.
- Replace {owner_address} with the wallet address from which the deployment will be made.
Example: python src/generator/run.py --end NESS -w -0 --case-sensitive UQCDrgGaI6gWK-qlyw69xWZosurGxrpRgIgSkVsgahUtxZR0

If the script successfully finds a match, you will see a message in the console like:
Found: EQC7PA9iWnUVWv001Drj3vTu-pmAkTc30OarHy5iDJ1uNESS salt: 7c9398f0999a96fe5480b5d573817255d53377a000be18d0fb47d090a5606dfe

Step 4: Copy the `salt` value from the console output and use it in the `SALT` constant below.
"""

from tonutils.client import TonapiClient
from tonutils.jetton import JettonMasterStandard
from tonutils.jetton.content import JettonOnchainContent
from tonutils.vanity import Vanity
from tonutils.wallet import WalletV4R2

# API key for accessing the Tonapi (obtainable from https://tonconsole.com)
API_KEY = ""

# Set to True for test network, False for main network
IS_TESTNET = True

# Mnemonic phrase used to connect the wallet
MNEMONIC: list[str] = []

# The salt for the vanity address
SALT = ""


async def main() -> None:
    client = TonapiClient(api_key=API_KEY, is_testnet=IS_TESTNET)
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
