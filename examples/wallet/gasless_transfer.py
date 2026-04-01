from ton_core import Address, NetworkGlobalID, to_nano

from tonutils.clients import TonapiClient
from tonutils.contracts import WalletV5R1

# Tonapi API key (required for gasless transfers)
# Get one at https://tonconsole.com/
API_KEY = "YOUR_API_KEY"

# Mnemonic phrase — 24 words (TON-native) or 12/18/24 words (BIP-39 import)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Jetton master contract address (identifies the token type)
# This jetton is used both for the transfer and for gas payment
# Supported jettons: check https://tonapi.io/v2/gasless/config via Tonapi
JETTON_MASTER_ADDRESS = Address("EQ...")

# Destination address (jetton recipient)
DESTINATION_ADDRESS = Address("UQ...")

# Jetton amount in base units (respects token decimals)
# Example: 1 USD₮ (6 decimals) → 1 * 10^6 = 1,000,000
JETTON_AMOUNT_TO_SEND = to_nano(1, decimals=6)


async def main() -> None:
    # Initialize Tonapi client (required for gasless transfers)
    # Gasless transfers are only supported via TonapiClient on MAINNET
    client = TonapiClient(network=NetworkGlobalID.MAINNET, api_key=API_KEY)
    await client.connect()

    # Create WalletV5R1 instance from mnemonic
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Gasless transfers are only available for WalletV5 (R1 and Beta)
    wallet, _, _, _ = WalletV5R1.from_mnemonic(client, MNEMONIC)

    # Step 1: Estimate the gasless transfer
    # Builds a jetton transfer message, validates provider and jetton support,
    # then sends it to the Tonapi gasless estimation endpoint.
    # The relay pays TON gas on behalf of the sender — commission is deducted
    # from the sender's jetton balance.
    #
    # Parameters mirror JettonTransferBuilder:
    # destination: recipient address (receives jettons)
    # jetton_amount: amount in base units (respects token decimals)
    # jetton_master_address: identifies which jetton to transfer (also used for gas)
    estimate = await wallet.gasless_estimate(
        destination=DESTINATION_ADDRESS,
        jetton_amount=JETTON_AMOUNT_TO_SEND,
        jetton_master_address=JETTON_MASTER_ADDRESS,
    )

    # Step 2: Review the estimation result before sending
    # The estimate contains relay commission, emulation trace, and risk assessment.
    # Always verify these values before signing — once sent, the transaction
    # is irreversible.
    #
    # estimate.commission — relay fee in nanocoins (deducted from jetton balance)
    # estimate.relay_address — address of the relay paying gas
    # estimate.valid_until — unix timestamp, transaction expires after this time
    # estimate.messages  — messages to sign (built by the relay)
    # estimate.emulation — full transaction emulation with trace and risk analysis:
    #   emulation["risk"]  — conservative upper bound on potential asset loss
    #   emulation["event"] — high-level actions (jetton transfer, etc.)
    #   emulation["trace"] — full transaction trace with all child transactions
    print(f"Commission: {estimate.commission} nanocoins")
    print(f"Valid until: {estimate.valid_until}")

    # Step 3: Sign and send via gasless relay
    # Builds an external message from the estimation, signs it with the wallet's
    # private key, and sends through the Tonapi gasless endpoint.
    await wallet.gasless_send(estimate)
    print("Gasless transfer sent!")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
