from tonutils.tonconnect.models._types import (
    A,
    BaseModel,
    Binary64,
    ChainId,
    TonAddress,
    TonPublicKey,
    WalletStateInit,
)
from tonutils.tonconnect.models.payload import SignDataPayload
from tonutils.tonconnect.models.proof import TonProofData


class SignDataPayloadDto(BaseModel):
    """Verified `signData` payload DTO for signature verification.

    Attributes:
        address: Wallet address.
        network: Network identifier.
        public_key: Wallet public key.
        wallet_state_init: Wallet `StateInit`.
        signature: Ed25519 signature (64 bytes).
        timestamp: Signing unix timestamp.
        domain: dApp domain.
        payload: Signed data payload.
    """

    address: TonAddress
    network: ChainId
    public_key: TonPublicKey = A("publicKey")
    wallet_state_init: WalletStateInit = A("walletStateInit")
    signature: Binary64
    timestamp: int
    domain: str
    payload: SignDataPayload


class TonProofPayloadDto(BaseModel):
    """Verified `ton_proof` payload DTO for signature verification.

    Attributes:
        address: Wallet address.
        network: Network identifier.
        public_key: Wallet public key.
        wallet_state_init: Wallet `StateInit`.
        proof: TON Proof data.
    """

    address: TonAddress
    network: ChainId
    public_key: TonPublicKey = A("publicKey")
    wallet_state_init: WalletStateInit = A("walletStateInit")
    proof: TonProofData
