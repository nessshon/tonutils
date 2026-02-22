from tonutils.tonconnect.models._types import (
    A,
    BaseModel,
    TonAddress,
    ChainId,
    TonPublicKey,
    WalletStateInit,
)


class Account(BaseModel):
    """Connected wallet account data.

    Attributes:
        address: Wallet address.
        network: Network identifier.
        public_key: Wallet public key.
        state_init: Wallet `StateInit`.
    """

    address: TonAddress
    network: ChainId
    public_key: TonPublicKey = A("publicKey")
    state_init: WalletStateInit = A("walletStateInit")
