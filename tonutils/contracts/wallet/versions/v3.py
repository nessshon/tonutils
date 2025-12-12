import typing as t

from pytoniq_core import Cell, WalletMessage, begin_cell

from tonutils.contracts.versions import ContractVersion
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.configs import WalletV3Config
from tonutils.contracts.wallet.methods import SeqnoGetMethod, GetPublicKeyGetMethod
from tonutils.contracts.wallet.params import WalletV3Params
from tonutils.contracts.wallet.tlb import WalletV3Data
from tonutils.utils import calc_valid_until


class _WalletV3(
    BaseWallet[
        WalletV3Data,
        WalletV3Config,
        WalletV3Params,
    ],
    SeqnoGetMethod,
    GetPublicKeyGetMethod,
):
    """Base implementation for Wallet V3 contracts."""

    _data_model = WalletV3Data
    """TlbScheme class for deserializing wallet state data."""

    _config_model = WalletV3Config
    """Configuration model class for this wallet version."""

    _params_model = WalletV3Params
    """Transaction parameters model class for this wallet version."""

    MAX_MESSAGES = 4
    """Maximum number of messages allowed in a single transaction."""

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV3Params] = None,
    ) -> Cell:
        """
        Build unsigned message cell for Wallet V3 transaction.

        :param messages: List of wallet messages (max 4 for V3)
        :param params: Optional wallet parameters (seqno, valid_until)
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

        for message in messages:
            cell.store_cell(message.serialize())

        return cell.end_cell()


class WalletV3R1(_WalletV3):
    """Wallet V3 Revision 1 contract."""

    VERSION = ContractVersion.WalletV3R1
    """Contract version identifier."""


class WalletV3R2(_WalletV3):
    """Wallet V3 Revision 2 contract."""

    VERSION = ContractVersion.WalletV3R2
    """Contract version identifier."""
