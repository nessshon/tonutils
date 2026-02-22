from tonutils.tonconnect.models import SignDataPayloadDto
from tonutils.tonconnect.utils.signing import VerifySignData

# Payload received from the frontend after the user signs arbitrary data via TonConnect
# Unlike TonProof (which is connection-time auth), signData is called explicitly
# to sign off-chain content — useful for agreeing to terms, authorizing actions, etc.
#
# address:         raw wallet address (workchain:hash format)
# network:         "-239" for mainnet, "-3" for testnet
# publicKey:       wallet's Ed25519 public key (hex)
# walletStateInit: base64-encoded wallet StateInit — used to derive and verify the public key
#                  even if the contract is not yet deployed on-chain (uninit state)
# signature:       Ed25519 signature over the canonical signing message (base64)
# timestamp:       Unix epoch (seconds) when the wallet signed — checked against valid_auth_time
# domain:          app domain the wallet signed for — must be in allowed_domains
# payload:         the data the user signed; supported types: text, binary, or cell
PAYLOAD = {
    "address": "0:83ae019a23a8162beaa5cb0ebdc56668b2eac6c6ba51808812915b206a152dc5",
    "network": "-239",
    "publicKey": "79c446597dbf81b9987e9059de95dc557bcd9e2c431a6db1677768783d0b99f7",
    "walletStateInit": "te6cckECFgEAArEAAgE0AgEAUYAAAAA///+IvOIjLL7fwNzMP0gs70ruKr3mzxYhjTbYs7u0PB6FzPugART/APSkE/S88sgLAwIBIAYEAQLyBQEeINcLH4IQc2lnbrry4Ip/EQIBSBAHAgEgCQgAGb5fD2omhAgKDrkPoCwCASANCgIBSAwLABGyYvtRNDXCgCAAF7Ml+1E0HHXIdcLH4AIBbg8OABmvHfaiaEAQ65DrhY/AABmtznaiaEAg65Drhf/AAtzQINdJwSCRW49jINcLHyCCEGV4dG69IYIQc2ludL2wkl8D4IIQZXh0brqOtIAg1yEB0HTXIfpAMPpE+Cj6RDBYvZFb4O1E0IEBQdch9AWDB/QOb6ExkTDhgEDXIXB/2zzgMSDXSYECgLmRMOBw4hIRAeaO8O2i7fshgwjXIgKDCNcjIIAg1yHTH9Mf0x/tRNDSANMfINMf0//XCgAK+QFAzPkQmiiUXwrbMeHywIffArNQB7Dy0IRRJbry4IVQNrry4Ib4I7vy0IgikvgA3gGkf8jKAMsfAc8Wye1UIJL4D95w2zzYEgP27aLt+wL0BCFukmwhjkwCIdc5MHCUIccAs44tAdcoIHYeQ2wg10nACPLgkyDXSsAC8uCTINcdBscSwgBSMLDy0InXTNc5MAGk6GwShAe78uCT10rAAPLgk+1V4tIAAcAAkVvg69csCBQgkXCWAdcsCBwS4lIQseMPINdKFRQTABCTW9sx4ddM0AByMNcsCCSOLSHy4JLSAO1E0NIAURO68tCPVFAwkTGcAYEBQNch1woA8uCO4sjKAFjPFsntVJPywI3iAJYB+kAB+kT4KPpEMFi68uCR7UTQgQFB1xj0BQSdf8jKAEAEgwf0U/Lgi44UA4MH9Fvy4Iwi1woAIW4Bs7Dy0JDiyFADzxYS9ADJ7VSiwRtT",
    "signature": "D802ocFTDfQsBtG8RDOI7jiBAfhr9J0GJxArXmbspB6WfzcyVsX/+iTjdCPObLEX9fAT/QE9EkeFusUvwAnoDA==",
    "timestamp": 1754503448,
    "domain": "github.com",
    "payload": {"type": "text", "text": "Hello from tonutils!"},
}


async def main() -> None:
    # Parse and validate the raw payload dict into a typed DTO
    payload = SignDataPayloadDto.model_validate(PAYLOAD)

    # Verify the signed data — raises BadSignatureError if any check fails:
    #   1. Public key is extracted from walletStateInit and matches publicKey field
    #   2. Address is derived from walletStateInit and matches address field
    #   3. Timestamp is within valid_auth_time window (prevents replay attacks)
    #   4. Domain is in allowed_domains (prevents cross-app reuse)
    #   5. Ed25519 signature over the canonical message is valid
    #      Message format varies by payload type: text/binary use SHA-256,
    #      cell payloads use a TL-B Cell hash with CRC32 schema fingerprint
    #
    # allowed_domains: list of domains your backend accepts — reject anything else
    # valid_auth_time: max age of the signature in seconds (keep short, 5 min typical)
    await VerifySignData(payload).verify(
        allowed_domains=["github.com"],
        valid_auth_time=5 * 60,  # 5 minutes
    )
    print("SignData verified")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
