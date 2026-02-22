import typing as t
from dataclasses import dataclass, asdict

from pytoniq_core import Cell

from tonutils.contracts.wallet.tlb import WalletV5SubwalletID
from tonutils.types import PublicKey, DEFAULT_SUBWALLET_ID


@dataclass
class BaseContractConfig:
    """Base configuration class for TON contracts."""


@dataclass
class BaseWalletConfig(BaseContractConfig):
    """Base configuration for TON wallet contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
    """

    public_key: t.Optional[PublicKey] = None

    def to_dict(self) -> t.Dict[str, t.Any]:
        """Convert configuration fields to a dictionary."""
        return asdict(self)


@dataclass
class WalletV1Config(BaseWalletConfig):
    """Configuration for Wallet v1 contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
        seqno: Sequence number for transaction ordering (default: 0).
    """

    seqno: int = 0


@dataclass
class WalletV2Config(BaseWalletConfig):
    """Configuration for Wallet v2 contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
        seqno: Sequence number for transaction ordering (default: 0).
    """

    seqno: int = 0


@dataclass
class WalletV3Config(BaseWalletConfig):
    """Configuration for Wallet v3 contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
        seqno: Sequence number for transaction ordering (default: 0).
        subwallet_id: Subwallet identifier for wallet isolation (default: 698983191).
    """

    seqno: int = 0
    subwallet_id: int = DEFAULT_SUBWALLET_ID


@dataclass
class WalletV4Config(BaseWalletConfig):
    """Configuration for Wallet v4 contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
        seqno: Sequence number for transaction ordering (default: 0).
        subwallet_id: Subwallet identifier for wallet isolation (default: 698983191).
        plugins: Optional dictionary cell containing installed plugins.
    """

    seqno: int = 0
    subwallet_id: int = DEFAULT_SUBWALLET_ID
    plugins: t.Optional[Cell] = None


@dataclass
class WalletV5BetaConfig(BaseWalletConfig):
    """Configuration for Wallet v5 Beta contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
        seqno: Sequence number for transaction ordering (default: 0).
        subwallet_id: Enhanced subwallet identifier with network and workchain info.
        plugins: Optional dictionary cell containing installed plugins.
    """

    seqno: int = 0
    subwallet_id: t.Optional[WalletV5SubwalletID] = None
    plugins: t.Optional[Cell] = None


@dataclass
class WalletV5Config(BaseWalletConfig):
    """Configuration for Wallet v5 contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
        is_signature_allowed: Whether signature authentication is enabled (default: True).
        seqno: Sequence number for transaction ordering (default: 0).
        subwallet_id: Enhanced subwallet identifier with network and workchain info.
        plugins: Optional dictionary cell containing installed plugins.
    """

    is_signature_allowed: bool = True
    seqno: int = 0
    subwallet_id: t.Optional[WalletV5SubwalletID] = None
    plugins: t.Optional[Cell] = None


@dataclass
class WalletHighloadV2Config(BaseWalletConfig):
    """Configuration for Highload Wallet v2 contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
        subwallet_id: Subwallet identifier for wallet isolation (default: 698983191).
        last_cleaned: Timestamp of last query cleanup operation (default: 0).
        old_queries: Optional dictionary cell storing processed query IDs for replay protection.
    """

    subwallet_id: int = DEFAULT_SUBWALLET_ID
    last_cleaned: int = 0
    old_queries: t.Optional[Cell] = None


@dataclass
class WalletHighloadV3Config(BaseWalletConfig):
    """Configuration for Highload Wallet v3 contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
        subwallet_id: Subwallet identifier for wallet isolation (default: 698983191).
        old_queries: Optional dictionary cell storing old processed query IDs.
        queries: Optional dictionary cell storing current processed query IDs.
        last_clean_time: Timestamp of last query cleanup operation (default: 0).
        timeout: Query expiration timeout in seconds (default: 300 seconds / 5 minutes).
    """

    subwallet_id: int = DEFAULT_SUBWALLET_ID
    old_queries: t.Optional[Cell] = None
    queries: t.Optional[Cell] = None
    last_clean_time: int = 0
    timeout: int = 60 * 5


@dataclass
class WalletPreprocessedV2Config(BaseWalletConfig):
    """Configuration for Preprocessed Wallet v2 contracts.

    Attributes:
        public_key: Ed25519 public key for the wallet.
        seqno: Sequence number for transaction ordering (default: 0).
    """

    seqno: int = 0
