import abc
import typing as t

from ton_core import (
    Address,
    AddressLike,
    Cell,
    ContractVersion,
    JettonMasterStablecoinData,
    JettonMasterStandardData,
    OffchainContent,
    OnchainContent,
    StateInit,
    WorkchainID,
    begin_cell,
    cell_hash,
    to_cell,
)

from tonutils.contracts.base import BaseContract
from tonutils.contracts.jetton.methods import (
    GetJettonDataGetMethod,
    GetNextAdminAddressGetMethod,
    GetWalletAddressGetMethod,
)

_D = t.TypeVar(
    "_D",
    bound=JettonMasterStandardData | JettonMasterStablecoinData,
)
_C = t.TypeVar(
    "_C",
    bound=OnchainContent | OffchainContent,
)

_DStandard = t.TypeVar("_DStandard", bound=JettonMasterStandardData)
_DStablecoin = t.TypeVar("_DStablecoin", bound=JettonMasterStablecoinData)

_CStandard = t.TypeVar("_CStandard", bound=OnchainContent | OffchainContent)
_CStablecoin = t.TypeVar("_CStablecoin", bound=OnchainContent)


class BaseJettonMaster(
    BaseContract[_D],
    GetWalletAddressGetMethod,
    GetJettonDataGetMethod,
    t.Generic[_D, _C],
    abc.ABC,
):
    """Base Jetton master contract (TEP-74).

    Stores Jetton metadata, total supply, admin address, and wallet code.
    """

    _data_model: type[_D]

    @property
    def jetton_wallet_code(self) -> Cell:
        """Code ``Cell`` for Jetton wallets managed by this master."""
        return self.state_data.jetton_wallet_code

    @property
    def admin_address(self) -> Address | None:
        """Admin address, or ``None``."""
        return t.cast("Address | None", self.state_data.admin_address)

    @property
    def total_supply(self) -> int:
        """Total supply of the Jetton in base units."""
        return self.state_data.total_supply

    @property
    def content(self) -> _C:
        """Jetton metadata content."""
        return t.cast("_C", self.state_data.content)

    @classmethod
    @abc.abstractmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
        **kwargs: t.Any,
    ) -> Cell:
        """Pack Jetton wallet data cell for address calculation.

        :param owner_address: Wallet owner's address.
        :param jetton_master_address: Master contract address.
        :param jetton_wallet_code: Wallet contract code.
        :return: Packed wallet data ``Cell``.
        """

    @classmethod
    def calculate_user_jetton_wallet_address(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell | str,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        """Calculate user's Jetton wallet address.

        :param owner_address: Wallet owner's address.
        :param jetton_master_address: Master contract address.
        :param jetton_wallet_code: Wallet contract code (``Cell`` or hex string).
        :param workchain: Target workchain.
        :return: Calculated wallet address.
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
    """Standard Jetton master contract (TEP-74)."""

    _data_model: type[_DStandard] = JettonMasterStandardData  # type: ignore[assignment]
    VERSION = ContractVersion.JettonMasterStandard

    @classmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
        **kwargs: t.Any,
    ) -> Cell:
        """Pack standard Jetton wallet data cell.

        :param owner_address: Wallet owner's address.
        :param jetton_master_address: Master contract address.
        :param jetton_wallet_code: Wallet contract code.
        :return: Packed wallet data ``Cell``.
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
    """Stablecoin Jetton master with admin-controlled minting."""

    _data_model: type[_DStablecoin] = JettonMasterStablecoinData  # type: ignore[assignment]
    VERSION = ContractVersion.JettonMasterStablecoin

    @classmethod
    def _pack_jetton_wallet_data(
        cls,
        owner_address: AddressLike,
        jetton_master_address: AddressLike,
        jetton_wallet_code: Cell,
        **kwargs: t.Any,
    ) -> Cell:
        """Pack stablecoin Jetton wallet data cell.

        :param owner_address: Wallet owner's address.
        :param jetton_master_address: Master contract address.
        :param jetton_wallet_code: Wallet contract code.
        :return: Packed wallet data ``Cell``.
        """
        cell = begin_cell()
        cell.store_uint(0, 4)
        cell.store_coins(0)
        cell.store_address(owner_address)
        cell.store_address(jetton_master_address)
        return cell.end_cell()


class JettonMasterStablecoinV2(JettonMasterStablecoin[_DStablecoin, _CStablecoin]):
    """Sharded stablecoin master with deterministic wallet addresses."""

    _SHARD_DEPTH: int = 8
    VERSION = ContractVersion.JettonMasterStablecoinV2

    @classmethod
    def _get_address_shard_prefix(cls, address: AddressLike) -> int:
        """Extract shard prefix from an address.

        :param address: Source address.
        :return: Shard prefix (8 bits).
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
        **kwargs: t.Any,
    ) -> Cell:
        """Pack stablecoin v2 Jetton wallet data cell.

        :param owner_address: Wallet owner's address.
        :param jetton_master_address: Master contract address.
        :param jetton_wallet_code: Wallet contract code.
        :return: Packed wallet data ``Cell``.
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
        jetton_wallet_code: Cell | str,
    ) -> Cell:
        """Calculate ``StateInit`` cell for sharded wallet.

        :param owner_address: Wallet owner's address.
        :param jetton_master_address: Master contract address.
        :param jetton_wallet_code: Wallet contract code (``Cell`` or hex string).
        :return: ``StateInit`` cell with shard depth.
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
        jetton_wallet_code: Cell | str,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
    ) -> Address:
        """Calculate user's sharded Jetton wallet address.

        :param owner_address: Wallet owner's address.
        :param jetton_master_address: Master contract address.
        :param jetton_wallet_code: Wallet contract code (``Cell`` or hex string).
        :param workchain: Target workchain.
        :return: Calculated sharded wallet address.
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
        return t.cast("Address", cell.end_cell().begin_parse().load_address())
