from tonutils.tonconnect.models._types import A, BaseModel, Binary64


class TonProofDomain(BaseModel):
    """Domain component of a TON Proof.

    Attributes:
        length_bytes: Domain string length in bytes.
        value: Domain string.
    """

    length_bytes: int = A("lengthBytes")
    value: str


class TonProofData(BaseModel):
    """TON Proof data from the wallet.

    Attributes:
        timestamp: Proof unix timestamp.
        domain: Signed domain.
        signature: Ed25519 signature (64 bytes).
        payload: Challenge payload string.
    """

    timestamp: int
    domain: TonProofDomain
    signature: Binary64
    payload: str
