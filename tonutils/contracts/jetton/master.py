import abc
import typing as t

from pytoniq_core import Address, Cell, StateInit, begin_cell

from tonutils.contracts.base import BaseContract
from tonutils.contracts.jetton.methods import (
    GetWalletAddressGetMethod,
    GetJettonDataGetMethod,
    GetNextAdminAddressGetMethod,
)
from tonutils.contracts.jetton.tlb import (
    JettonMasterStablecoinData,
    JettonMasterStandardData,
)
from tonutils.contracts.nft.tlb import OnchainContent, OffchainContent
from tonutils.contracts.versions import ContractVersion
from tonutils.types import AddressLike, WorkchainID
from tonutils.utils import cell_hash, to_cell

_D = t.TypeVar(
    "_D",
    bound=t.Union[
        JettonMasterStandardData,
        JettonMasterStablecoinData,
    ],
)
_C = t.TypeVar(
    "_C",
    bound=t.Union[
        OnchainContent,
        OffchainContent,
    ],
)

_DStandard = t.TypeVar("_DStandard", bound=JettonMasterStandardData)
_DStablecoin = t.TypeVar("_DStablecoin", bound=JettonMasterStablecoinData)

_CStandard = t.TypeVar("_CStandard", bound=t.Union[OnchainContent, OffchainContent])
_CStablecoin = t.TypeVar("_CStablecoin", bound=OnchainContent)


class BaseJettonMaster(
    BaseContract[_D],
    GetWalletAddressGetMethod,
    GetJettonDataGetMethod,
    t.Generic[_D, _C],
    abc.ABC,
):
    _data_model: t.Type[_D]

    @property
    def jetton_wallet_code(self) -> Cell:
        return self.state_data.jetton_wallet_code

    @property
    def admin_address(self) -> t.Optional[Address]:
        return self.state_data.admin_address

    @property
    def total_supply(self) -> int:
        return self.state_data.total_supply

    @property
    def content(self) -> _C:
        return self.state_data.content

    @classmethod
    @abc.abstractmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: t.Union[Cell, str],
    ) -> Cell: ...

    @classmethod
    def calculate_user_jetton_wallet_address(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: t.Union[Cell, str],
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        code = to_cell(jetton_wallet_code)
        data = cls._pack_jetton_wallet_data(
            owner_address=owner_address,
            jetton_master_address=jetton_master_address,
            jetton_wallet_code=code,
        )
        state_init = StateInit(code=code, data=data)
        return Address((workchain.value, state_init.serialize().hash))


class JettonMasterStandard(BaseJettonMaster[_DStandard, _CStandard]):
    _data_model = JettonMasterStandardData
    VERSION = ContractVersion.JettonMasterStandard

    @classmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Cell:
        cell = begin_cell()
        cell.store_coins(0)
        cell.store_address(owner_address)
        cell.store_address(jetton_master_address)
        cell.store_ref(jetton_wallet_code)
        return cell.end_cell()


class JettonMasterStablecoin(
    BaseJettonMaster[_DStablecoin, _CStablecoin],
    GetNextAdminAddressGetMethod,
):
    _data_model = JettonMasterStablecoinData
    VERSION = ContractVersion.JettonMasterStablecoin

    @classmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
    ) -> Cell:
        cell = begin_cell()
        cell.store_uint(0, 4)
        cell.store_coins(0)
        cell.store_address(owner_address)
        cell.store_address(jetton_master_address)
        return cell.end_cell()


class JettonMasterStablecoinV2(JettonMasterStablecoin):
    _SHARD_DEPTH: int = 8
    VERSION = ContractVersion.JettonMasterStablecoinV2

    @classmethod
    def _get_address_shard_prefix(cls, address: AddressLike) -> int:
        if isinstance(address, str):
            address = Address(address)
        cs = address.to_cell().begin_parse()
        return cs.skip_bits(3 + 8).preload_uint(8)

    @classmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
    ) -> Cell:
        cell = begin_cell()
        cell.store_coins(0)
        cell.store_address(owner_address)
        cell.store_address(jetton_master_address)
        return cell.end_cell()

    @classmethod
    def _calculate_jetton_wallet_state_init_cell(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: t.Union[Cell, str],
    ) -> Cell:
        code = to_cell(jetton_wallet_code)
        data = cls._pack_jetton_wallet_data(
            owner_address=owner_address,
            jetton_master_address=jetton_master_address,
            jetton_wallet_code=code,
        )
        cell = begin_cell()
        cell.store_uint(1, 1)
        cell.store_uint(cls._SHARD_DEPTH, 5)
        cell.store_uint(0, 1)
        cell.store_maybe_ref(code)
        cell.store_maybe_ref(data)
        cell.store_uint(0, 1)
        return cell.end_cell()

    @classmethod
    def calculate_user_jetton_wallet_address(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: t.Union[Cell, str],
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        state_init_cell = cls._calculate_jetton_wallet_state_init_cell(
            owner_address=owner_address,
            jetton_master_address=jetton_master_address,
            jetton_wallet_code=jetton_wallet_code,
        )
        shard_prefix = cls._get_address_shard_prefix(owner_address)
        mask = (1 << (256 - cls._SHARD_DEPTH)) - 1
        prefix_less = cell_hash(state_init_cell) & mask
        cell = begin_cell()
        cell.store_uint(4, 3)
        cell.store_int(workchain.value, 8)
        cell.store_uint(shard_prefix, cls._SHARD_DEPTH)
        cell.store_uint(prefix_less, 256 - cls._SHARD_DEPTH)
        return cell.end_cell().begin_parse().load_address()
