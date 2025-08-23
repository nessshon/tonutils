"""
Example: Verifying Ton Proof using `verify_ton_proof` from tonutils.

The TonConnect client provides the signed proof payload (see `EXAMPLE_DATA` below),
which must be collected on the client and sent to your backend for verification.

By default, `verify_ton_proof` will try to extract the public key from the provided `state_init`.
If that fails (e.g. for custom wallets), you can supply a fallback resolver via
`get_wallet_pubkey(address: str) -> bytes`.
"""
from tonutils.tonconnect.models import CheckProofRequestDto
from tonutils.tonconnect.utils.verifiers import verify_ton_proof

# This is a sample proof payload collected from the TonConnect client (DApp frontend)
EXAMPLE_DATA = {
    "address": "0:83ae019a23a8162beaa5cb0ebdc56668b2eac6c6ba51808812915b206a152dc5",
    "state_init": "te6cckECFgEAArEAAgE0AgEAUYAAAAA///+IvOIjLL7fwNzMP0gs70ruKr3mzxYhjTbYs7u0PB6FzPugART/APSkE/S88sgLAwIBIAYEAQLyBQEeINcLH4IQc2lnbrry4Ip/EQIBSBAHAgEgCQgAGb5fD2omhAgKDrkPoCwCASANCgIBSAwLABGyYvtRNDXCgCAAF7Ml+1E0HHXIdcLH4AIBbg8OABmvHfaiaEAQ65DrhY/AABmtznaiaEAg65Drhf/AAtzQINdJwSCRW49jINcLHyCCEGV4dG69IYIQc2ludL2wkl8D4IIQZXh0brqOtIAg1yEB0HTXIfpAMPpE+Cj6RDBYvZFb4O1E0IEBQdch9AWDB/QOb6ExkTDhgEDXIXB/2zzgMSDXSYECgLmRMOBw4hIRAeaO8O2i7fshgwjXIgKDCNcjIIAg1yHTH9Mf0x/tRNDSANMfINMf0//XCgAK+QFAzPkQmiiUXwrbMeHywIffArNQB7Dy0IRRJbry4IVQNrry4Ib4I7vy0IgikvgA3gGkf8jKAMsfAc8Wye1UIJL4D95w2zzYEgP27aLt+wL0BCFukmwhjkwCIdc5MHCUIccAs44tAdcoIHYeQ2wg10nACPLgkyDXSsAC8uCTINcdBscSwgBSMLDy0InXTNc5MAGk6GwShAe78uCT10rAAPLgk+1V4tIAAcAAkVvg69csCBQgkXCWAdcsCBwS4lIQseMPINdKFRQTABCTW9sx4ddM0AByMNcsCCSOLSHy4JLSAO1E0NIAURO68tCPVFAwkTGcAYEBQNch1woA8uCO4sjKAFjPFsntVJPywI3iAJYB+kAB+kT4KPpEMFi68uCR7UTQgQFB1xj0BQSdf8jKAEAEgwf0U/Lgi44UA4MH9Fvy4Iwi1woAIW4Bs7Dy0JDiyFADzxYS9ADJ7VSiwRtT",
    "public_key": "79c446597dbf81b9987e9059de95dc557bcd9e2c431a6db1677768783d0b99f7",
    "proof": {
        "domain": {
            "lengthBytes": 10,
            "value": "github.com",
        },
        "payload": "f85774c9762007d20000000068941ae3",
        "signature": "d8GGkzgRbyPCiAt4a2EN+xiNK6fLHo/ptQdDT3YQcUD4cg3TUnE2Airf37y+xRkEP/aiQq38ytS4Ho4ZDHM5CQ==",
        "timestamp": 1754535788,
    }
}


async def get_wallet_pubkey(address: str) -> bytes:
    """
    Resolve the wallet's public key using its address.

    :param address: Wallet address in raw TON format.
    :return: Public key as raw bytes.

    TODO:
        - Use Toncenter, TonAPI, or LiteClient to fetch pubkey (e.g., via `get_public_key`)
        - Add caching or fallback strategies
        - Properly handle network and decoding errors
    """
    raise NotImplementedError("Implement public key resolver based on wallet address.")


async def main() -> None:
    payload = CheckProofRequestDto.from_dict(EXAMPLE_DATA)

    # `verify_ton_proof` automatically:
    # - Validates domain and timestamp
    # - Verifies the signature using Ed25519
    # - Extracts the public key from `state_init`
    # - Checks that derived contract address matches the provided address

    is_valid = await verify_ton_proof(
        payload=payload,
        allowed_domains=["github.com", "localhost:5173"],
        valid_auth_time=15 * 60,  # Signature expiration window (in seconds)
        # get_wallet_pubkey=get_wallet_pubkey  # Uncomment to provide custom pubkey resolver
    )

    print("Valid proof" if is_valid else "Invalid proof")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
