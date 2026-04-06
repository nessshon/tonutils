from ton_core import Address, NetworkGlobalID, NFTDestroyBody, to_nano

from tonutils.clients import ToncenterClient
from tonutils.contracts import WalletV4R2

# Mnemonic phrase — 24 words (TON-native) or 12/18/24 words (BIP-39 import)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# NFT item address to destroy
NFT_ITEM_ADDRESS = Address("EQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be NFT owner to destroy successfully (per TEP-85)
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Construct destroy message body
    body = NFTDestroyBody()

    # Send destroy transaction to NFT item contract
    # destination: NFT item contract address
    # body: serialized destroy message
    # amount: TON attached for gas fees (0.05 TON typical)
    msg = await wallet.transfer(
        destination=NFT_ITEM_ADDRESS,
        body=body.serialize(),
        amount=to_nano(0.05),
    )

    # Display destroyed NFT item address
    print(f"NFT item address: {NFT_ITEM_ADDRESS.to_str()}")

    # Normalized hash of the signed external message (computed locally before sending)
    # Not a blockchain transaction hash — use it to track whether the message
    # was accepted on-chain (e.g. via explorers, API queries, or your own checks)
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
