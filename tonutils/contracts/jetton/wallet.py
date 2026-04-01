import typing as t

from ton_core import (
    Address,
    ContractVersion,
    JettonWalletStablecoinData,
    JettonWalletStablecoinV2Data,
    JettonWalletStandardData,
)

from tonutils.contracts.base import BaseContract
from tonutils.contracts.jetton.methods import (
    GetStatusGetMethod,
    GetWalletDataGetMethod,
)

_D = t.TypeVar(
    "_D",
    bound=JettonWalletStandardData
    | JettonWalletStablecoinData
    | JettonWalletStablecoinV2Data,
)


class BaseJettonWallet(
    BaseContract[_D],
    GetWalletDataGetMethod,
):
    """Base Jetton wallet contract (TEP-74).

    Holds the Jetton balance and references the owner and master addresses.
    """

    _data_model: type[_D]

    @property
    def jetton_balance(self) -> int:
        """Current Jetton balance in base units."""
        return self.state_data.balance

    @property
    def owner_address(self) -> Address:
        """Owner address of this Jetton wallet."""
        return t.cast("Address", self.state_data.owner_address)

    @property
    def jetton_master_address(self) -> Address:
        """Jetton master contract address."""
        return t.cast("Address", self.state_data.jetton_master_address)


class JettonWalletStandard(BaseJettonWallet[JettonWalletStandardData]):
    """Standard Jetton wallet contract (TEP-74)."""

    _data_model = JettonWalletStandardData
    VERSION = ContractVersion.JettonWalletStandard


class JettonWalletStablecoin(
    BaseJettonWallet[JettonWalletStablecoinData],
    GetStatusGetMethod,
):
    """Stablecoin Jetton wallet with admin-controlled status field."""

    _data_model = JettonWalletStablecoinData
    VERSION = ContractVersion.JettonWalletStablecoin


class JettonWalletStablecoinV2(BaseJettonWallet[JettonWalletStablecoinV2Data]):
    """Sharded stablecoin wallet."""

    _data_model = JettonWalletStablecoinV2Data
    VERSION = ContractVersion.JettonWalletStablecoinV2
