import typing as t

from pytoniq_core import Address

from tonutils.contracts.base import BaseContract
from tonutils.contracts.jetton.methods import (
    GetStatusGetMethod,
    GetWalletDataGetMethod,
)
from tonutils.contracts.jetton.tlb import (
    JettonWalletStandardData,
    JettonWalletStablecoinData,
    JettonWalletStablecoinV2Data,
)
from tonutils.contracts.versions import ContractVersion

_D = t.TypeVar(
    "_D",
    bound=t.Union[
        JettonWalletStandardData,
        JettonWalletStablecoinData,
        JettonWalletStablecoinV2Data,
    ],
)


class BaseJettonWallet(
    BaseContract[_D],
    GetWalletDataGetMethod,
):
    """Base implementation for Jetton wallet contracts."""

    _data_model: t.Type[_D]
    """TlbScheme class for deserializing wallet state data."""

    @property
    def jetton_balance(self) -> int:
        """
        Current Jetton balance in this wallet.

        :return: Balance in smallest Jetton units
        """
        return self.state_data.balance

    @property
    def owner_address(self) -> Address:
        """
        Owner address of this Jetton wallet.

        :return: Owner's wallet address
        """
        return self.state_data.owner_address

    @property
    def jetton_master_address(self) -> Address:
        """
        Jetton master contract address.

        :return: Master contract address for this Jetton
        """
        return self.state_data.jetton_master_address


class JettonWalletStandard(BaseJettonWallet[JettonWalletStandardData]):
    """Standard Jetton wallet contract."""

    _data_model = JettonWalletStandardData
    """TlbScheme class for deserializing wallet state data."""

    VERSION = ContractVersion.JettonWalletStandard
    """Contract version identifier."""


class JettonWalletStablecoin(
    BaseJettonWallet[JettonWalletStablecoinData],
    GetStatusGetMethod,
):
    """Stablecoin Jetton wallet contract."""

    _data_model = JettonWalletStablecoinData
    """TlbScheme class for deserializing wallet state data."""

    VERSION = ContractVersion.JettonWalletStablecoin
    """Contract version identifier."""


class JettonWalletStablecoinV2(BaseJettonWallet[JettonWalletStablecoinV2Data]):
    """Stablecoin V2 Jetton wallet contract."""

    _data_model = JettonWalletStablecoinV2Data
    """TlbScheme class for deserializing wallet state data."""

    VERSION = ContractVersion.JettonWalletStablecoinV2
    """Contract version identifier."""
