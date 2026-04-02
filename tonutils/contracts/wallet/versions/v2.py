from __future__ import annotations

from ton_core import (
    Cell,
    ContractVersion,
    WalletMessage,
    WalletV2Config,
    WalletV2Data,
    WalletV2Params,
    begin_cell,
    calc_valid_until,
)

from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.methods import GetPublicKeyGetMethod, SeqnoGetMethod


class _WalletV2(
    BaseWallet[
        WalletV2Data,
        WalletV2Config,
        WalletV2Params,
    ],
    SeqnoGetMethod,
    GetPublicKeyGetMethod,
):
    """Wallet v2 -- adds valid_until expiration for replay protection."""

    _data_model = WalletV2Data
    _config_model = WalletV2Config
    _params_model = WalletV2Params
    MAX_MESSAGES = 4

    async def _build_msg_cell(
        self,
        messages: list[WalletMessage],
        params: WalletV2Params | None = None,
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
        cell.store_uint(seqno, 32)
        cell.store_uint(valid_until, 32)

        for message in messages:
            cell.store_cell(message.serialize())

        return cell.end_cell()


class WalletV2R1(_WalletV2):
    """Wallet v2 Revision 1."""

    VERSION = ContractVersion.WalletV2R1


class WalletV2R2(_WalletV2):
    """Wallet v2 Revision 2."""

    VERSION = ContractVersion.WalletV2R2
