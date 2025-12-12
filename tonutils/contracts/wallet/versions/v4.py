import typing as t

from pytoniq_core import Cell, WalletMessage, begin_cell

from tonutils.contracts.versions import ContractVersion
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.configs import WalletV4Config
from tonutils.contracts.wallet.methods import (
    SeqnoGetMethod,
    GetPublicKeyGetMethod,
    GetSubwalletIDGetMethod,
    GetPluginListGetMethod,
    IsPluginInstalledGetMethod,
)
from tonutils.contracts.wallet.params import WalletV4Params
from tonutils.contracts.wallet.tlb import WalletV4Data
from tonutils.utils import calc_valid_until


class _WalletV4(
    BaseWallet[
        WalletV4Data,
        WalletV4Config,
        WalletV4Params,
    ],
    SeqnoGetMethod,
    GetPublicKeyGetMethod,
    GetSubwalletIDGetMethod,
    GetPluginListGetMethod,
    IsPluginInstalledGetMethod,
):
    """Base implementation for Wallet V4 contracts."""

    _config_model = WalletV4Config
    """Configuration model class for this wallet version."""

    _data_model = WalletV4Data
    """TlbScheme class for deserializing wallet state data."""

    _params_model = WalletV4Params
    """Transaction parameters model class for this wallet version."""

    MAX_MESSAGES = 4
    """Maximum number of messages allowed in a single transaction."""

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV4Params] = None,
    ) -> Cell:
        """
        Build unsigned message cell for Wallet V4 transaction.

        :param messages: List of wallet messages (max 4 for V4)
        :param params: Optional wallet parameters (seqno, valid_until, op_code)
        :return: Unsigned message cell ready for signing
        """
        params = params or self._params_model()

        seqno = (
            params.seqno
            if params.seqno is not None
            else self.state_data.seqno if self.is_active else 0
        )
        valid_until = (
            params.valid_until
            if params.valid_until is not None
            else calc_valid_until(seqno)
        )

        cell = begin_cell()
        cell.store_uint(self.config.subwallet_id, 32)
        cell.store_uint(valid_until, 32)
        cell.store_uint(seqno, 32)
        cell.store_uint(params.op_code, 8)

        for message in messages:
            cell.store_cell(message.serialize())

        return cell.end_cell()


class WalletV4R1(_WalletV4):
    """Wallet V4 Revision 1 contract."""

    VERSION = ContractVersion.WalletV4R1
    """Contract version identifier."""


class WalletV4R2(_WalletV4):
    """Wallet V4 Revision 2 contract."""

    VERSION = ContractVersion.WalletV4R2
    """Contract version identifier."""
