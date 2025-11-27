import typing as t
from dataclasses import dataclass, asdict

from pytoniq_core import Cell

from tonutils.contracts.wallet.tlb import WalletV5SubwalletID
from tonutils.types import PublicKey, DEFAULT_SUBWALLET_ID


@dataclass
class BaseContractConfig: ...


@dataclass
class BaseWalletConfig(BaseContractConfig):
    public_key: t.Optional[PublicKey] = None

    def to_dict(self) -> t.Dict[str, t.Any]:
        return asdict(self)


@dataclass
class WalletV1Config(BaseWalletConfig):
    seqno: int = 0


@dataclass
class WalletV2Config(BaseWalletConfig):
    seqno: int = 0


@dataclass
class WalletV3Config(BaseWalletConfig):
    seqno: int = 0
    subwallet_id: int = DEFAULT_SUBWALLET_ID


@dataclass
class WalletV4Config(BaseWalletConfig):
    seqno: int = 0
    subwallet_id: int = DEFAULT_SUBWALLET_ID
    plugins: t.Optional[Cell] = None


@dataclass
class WalletV5BetaConfig(BaseWalletConfig):
    seqno: int = 0
    subwallet_id: t.Optional[WalletV5SubwalletID] = None
    plugins: t.Optional[Cell] = None


@dataclass
class WalletV5Config(BaseWalletConfig):
    is_signature_allowed: bool = True
    seqno: int = 0
    subwallet_id: t.Optional[WalletV5SubwalletID] = None
    plugins: t.Optional[Cell] = None


@dataclass
class WalletHighloadV2Config(BaseWalletConfig):
    subwallet_id: int = DEFAULT_SUBWALLET_ID
    last_cleaned: int = 0
    old_queries: t.Optional[Cell] = None


@dataclass
class WalletHighloadV3Config(BaseWalletConfig):
    subwallet_id: int = DEFAULT_SUBWALLET_ID
    old_queries: t.Optional[Cell] = None
    queries: t.Optional[Cell] = None
    last_clean_time: int = 0
    timeout: int = 60 * 5


@dataclass
class WalletPreprocessedV2Config(BaseWalletConfig):
    seqno: int = 0
