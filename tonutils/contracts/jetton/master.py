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
    """Base implementation for Jetton master contracts."""

    _data_model: t.Type[_D]
    """TlbScheme class for deserializing master state data."""

    @property
    def jetton_wallet_code(self) -> Cell:
        """
        Code cell for Jetton wallets managed by this master.

        :return: Wallet contract code
        """
        return self.state_data.jetton_wallet_code

    @property
    def admin_address(self) -> t.Optional[Address]:
        """
        Admin address of this Jetton master.

        :return: Admin's wallet address or None if no admin
        """
        return self.state_data.admin_address

    @property
    def total_supply(self) -> int:
        """
        Total supply of this Jetton.

        :return: Total supply in base units
        """
        return self.state_data.total_supply

    @property
    def content(self) -> _C:
        """
        Jetton metadata content.

        :return: Onchain or offchain content with token metadata
        """
        return self.state_data.content

    @classmethod
    @abc.abstractmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: t.Union[Cell, str],
    ) -> Cell:
        """
        Pack Jetton wallet data cell for address calculation.

        :param owner_address: Wallet owner's address
        :param jetton_master_address: Master contract address
        :param jetton_wallet_code: Wallet contract code
        :return: Packed wallet data cell
        """

    @classmethod
    def calculate_user_jetton_wallet_address(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: t.Union[Cell, str],
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        """
        Calculate user's Jetton wallet address.

        :param owner_address: Wallet owner's address
        :param jetton_master_address: Master contract address
        :param jetton_wallet_code: Wallet contract code (Cell or hex string)
        :param workchain: Target workchain (default: BASECHAIN)
        :return: Calculated wallet address
        """

        code = to_cell(jetton_wallet_code)
        data = cls._pack_jetton_wallet_data(
            owner_address=owner_address,
            jetton_master_address=jetton_master_address,
            jetton_wallet_code=code,
        )
        state_init = StateInit(code=code, data=data)
        return Address((workchain.value, state_init.serialize().hash))


class JettonMasterStandard(BaseJettonMaster[_DStandard, _CStandard]):
    """Standard Jetton master contract."""

    _data_model = JettonMasterStandardData
    """TlbScheme class for deserializing master state data."""

    VERSION = ContractVersion.JettonMasterStandard
    """Contract version identifier."""

    @classmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Cell:
        """
        Pack standard Jetton wallet data cell.

        :param owner_address: Wallet owner's address
        :param jetton_master_address: Master contract address
        :param jetton_wallet_code: Wallet contract code
        :param workchain: Target workchain (default: BASECHAIN)
        :return: Packed wallet data cell
        """
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
    """Stablecoin Jetton master contract."""

    _data_model = JettonMasterStablecoinData
    """TlbScheme class for deserializing master state data."""

    VERSION = ContractVersion.JettonMasterStablecoin
    """Contract version identifier."""

    @classmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
    ) -> Cell:
        """
        Pack stablecoin Jetton wallet data cell.

        :param owner_address: Wallet owner's address
        :param jetton_master_address: Master contract address
        :param jetton_wallet_code: Wallet contract code
        :return: Packed wallet data cell with status field
        """
        cell = begin_cell()
        cell.store_uint(0, 4)
        cell.store_coins(0)
        cell.store_address(owner_address)
        cell.store_address(jetton_master_address)
        return cell.end_cell()


class JettonMasterStablecoinV2(JettonMasterStablecoin):
    """Stablecoin V2 Jetton master contract."""

    _SHARD_DEPTH: int = 8
    """Number of bits used for address sharding."""

    VERSION = ContractVersion.JettonMasterStablecoinV2
    """Contract version identifier."""

    @classmethod
    def _get_address_shard_prefix(cls, address: AddressLike) -> int:
        """
        Extract shard prefix from address for sharded wallet calculation.

        :param address: Address to extract prefix from
        :return: Shard prefix (8 bits)
        """
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
        """
        Pack stablecoin V2 Jetton wallet data cell.

        :param owner_address: Wallet owner's address
        :param jetton_master_address: Master contract address
        :param jetton_wallet_code: Wallet contract code
        :return: Packed wallet data cell
        """
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
        """
        Calculate StateInit cell for sharded wallet.

        :param owner_address: Wallet owner's address
        :param jetton_master_address: Master contract address
        :param jetton_wallet_code: Wallet contract code (Cell or hex string)
        :return: StateInit cell with shard depth
        """
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
        """
        Calculate user's sharded Jetton wallet address.

        Uses shard prefix from owner address for load distribution.

        :param owner_address: Wallet owner's address
        :param jetton_master_address: Master contract address
        :param jetton_wallet_code: Wallet contract code (Cell or hex string)
        :param workchain: Target workchain (default: BASECHAIN)
        :return: Calculated sharded wallet address
        """
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
