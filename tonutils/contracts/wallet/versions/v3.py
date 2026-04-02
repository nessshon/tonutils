from ton_core import (
    Cell,
    ContractVersion,
    WalletMessage,
    WalletV3Config,
    WalletV3Data,
    WalletV3Params,
    begin_cell,
    calc_valid_until,
)

from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.methods import GetPublicKeyGetMethod, SeqnoGetMethod


class _WalletV3(
    BaseWallet[
        WalletV3Data,
        WalletV3Config,
        WalletV3Params,
    ],
    SeqnoGetMethod,
    GetPublicKeyGetMethod,
):
    """Wallet v3 -- adds subwallet ID for multiple wallets from one key."""

    _data_model = WalletV3Data
    _config_model = WalletV3Config
    _params_model = WalletV3Params
    MAX_MESSAGES = 4

    async def _build_msg_cell(
        self,
        messages: list[WalletMessage],
        params: WalletV3Params | None = None,
    ) -> Cell:
        """Build unsigned message cell.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or ``None``.
        :return: Unsigned message cell.
        """
        params = params or self._params_model()

        seqno = params.seqno if params.seqno is not None else self.state_data.seqno if self.is_active else 0
        valid_until = params.valid_until if params.valid_until is not None else calc_valid_until(seqno)

        cell = begin_cell()
        cell.store_uint(self.config.subwallet_id, 32)
        cell.store_uint(valid_until, 32)
        cell.store_uint(seqno, 32)

        for message in messages:
            cell.store_cell(message.serialize())

        return cell.end_cell()


class WalletV3R1(_WalletV3):
    """Wallet v3 Revision 1."""

    VERSION = ContractVersion.WalletV3R1


class WalletV3R2(_WalletV3):
    """Wallet v3 Revision 2."""

    VERSION = ContractVersion.WalletV3R2
