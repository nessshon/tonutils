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
    _data_model: t.Type[_D]

    @property
    def jetton_balance(self) -> int:
        return self.state_data.balance

    @property
    def owner_address(self) -> Address:
        return self.state_data.owner_address

    @property
    def jetton_master_address(self) -> Address:
        return self.state_data.jetton_master_address


class JettonWalletStandard(BaseJettonWallet[JettonWalletStandardData]):
    _data_model = JettonWalletStandardData
    VERSION = ContractVersion.JettonWalletStandard


class JettonWalletStablecoin(
    BaseJettonWallet[JettonWalletStablecoinData],
    GetStatusGetMethod,
):
    _data_model = JettonWalletStablecoinData
    VERSION = ContractVersion.JettonWalletStablecoin


class JettonWalletStablecoinV2(BaseJettonWallet[JettonWalletStablecoinV2Data]):
    _data_model = JettonWalletStablecoinV2Data
    VERSION = ContractVersion.JettonWalletStablecoinV2
