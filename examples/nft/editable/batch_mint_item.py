from pytoniq_core import Address

from tonutils.clients import ToncenterHttpClient
from tonutils.contracts import (
    NFTCollectionBatchMintItemBody,
    NFTCollectionEditable,
    NFTItemEditable,
    NFTItemEditableMintRef,
    OffchainItemContent,
    WalletV4R2,
)
from tonutils.types import NetworkGlobalID
from tonutils.utils import to_nano

# 24-word mnemonic phrase (BIP-39 or TON-specific)
# Used to derive the wallet's private key
MNEMONIC = "word1 word2 word3 ..."

# Starting index for batch minting
# Items will be minted with sequential indices: MINT_FROM_INDEX, MINT_FROM_INDEX+1, ...
MINT_FROM_INDEX = 0

# List of (owner, editor) address pairs for batch-minted Editable NFT items
# Each tuple: (owner_address, editor_address)
#   owner_address: receives the Editable NFT
#   editor_address: can modify item metadata
# Array length determines total items minted in single transaction
NFT_ITEM_OWNERS_AND_EDITORS = [
    (Address("UQ..."), Address("UQ...")),
    (Address("UQ..."), Address("UQ...")),
    (Address("UQ..."), Address("UQ...")),
]

# Deployed NFT collection contract address
NFT_COLLECTION_ADDRESS = Address("EQ...")


async def main() -> None:
    # Initialize HTTP client for TON blockchain interaction
    # NetworkGlobalID.MAINNET (-239) for production
    # NetworkGlobalID.TESTNET (-3) for testing
    client = ToncenterHttpClient(network=NetworkGlobalID.MAINNET)
    await client.connect()

    # Create wallet instance from mnemonic (full access mode)
    # Returns: (wallet, public_key, private_key, mnemonic)
    # Wallet must be collection owner to mint successfully
    wallet, _, _, _ = WalletV4R2.from_mnemonic(client, MNEMONIC)

    # Get default Editable NFT item code
    nft_item_code = NFTItemEditable.get_default_code()
    nft_items_count = len(NFT_ITEM_OWNERS_AND_EDITORS)
    nft_items_refs = []

    # Build initialization data for each Editable NFT item
    # Iterates through (owner, editor) pairs with sequential indices starting from MINT_FROM_INDEX
    for nft_item_index, (owner_address, editor_address) in enumerate(
        NFT_ITEM_OWNERS_AND_EDITORS, start=MINT_FROM_INDEX
    ):
        # Create off-chain content structure
        # suffix_uri: appended to collection's base URI to form full metadata URL
        # Example: "0.json", "1.json", "2.json" for sequential items
        nft_item_ref = NFTItemEditableMintRef(
            owner_address=owner_address,
            editor_address=editor_address,
            content=OffchainItemContent(suffix_uri=f"{nft_item_index}.json"),
        )
        nft_items_refs.append(nft_item_ref.serialize())

    # Construct batch mint message body
    # items_refs: array of serialized initialization data for all items
    # from_index: starting index for batch (items get sequential indices)
    # forward_amount: nanotons forwarded to each newly deployed item (covers initial storage fees)
    #   Typical: 0.01 TON per item ensures each has balance for storage rent
    body = NFTCollectionBatchMintItemBody(
        items_refs=nft_items_refs,
        from_index=MINT_FROM_INDEX,
        forward_amount=to_nano(0.01),
    )

    # Send batch mint transaction to collection contract
    # destination: collection contract address
    # amount: TON attached to message (covers gas + forward_amount for all items)
    #   Formula: 0.25 TON × items_count (scales with batch size)
    # body: serialized batch mint message
    msg = await wallet.transfer(
        destination=NFT_COLLECTION_ADDRESS,
        amount=to_nano(0.25) * nft_items_count,
        body=body.serialize(),
    )

    # Calculate and display addresses for all minted Editable NFT items
    for nft_item_index in range(MINT_FROM_INDEX, MINT_FROM_INDEX + nft_items_count):
        nft_item_address = NFTCollectionEditable.calculate_nft_item_address(
            index=nft_item_index,
            nft_item_code=nft_item_code,
            collection_address=NFT_COLLECTION_ADDRESS,
        )
        print(f"NFT item address ({nft_item_index}): {nft_item_address.to_str()}")

    # Transaction hash for tracking on blockchain explorers
    # Use tonviewer.com or tonscan.org to view transaction
    print(f"Transaction hash: {msg.normalized_hash}")

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
