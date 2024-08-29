from ._base import Wallet

from .highload import HighloadWalletV2, HighloadWalletV3
from .v3 import WalletV3R1, WalletV3R2
from .v4 import WalletV4R1, WalletV4R2
from .v5 import WalletV5R1

__all__ = [
    "Wallet",

    "HighloadWalletV2",
    "HighloadWalletV3",
    "WalletV3R1",
    "WalletV3R2",
    "WalletV4R1",
    "WalletV4R2",
    "WalletV5R1",
]
