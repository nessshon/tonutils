from ton_core import (
    Cell,
    ContractVersion,
    WalletMessage,
    WalletV4Config,
    WalletV4Data,
    WalletV4Params,
    begin_cell,
    calc_valid_until,
)

from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.methods import (
    GetPluginListGetMethod,
    GetPublicKeyGetMethod,
    GetSubwalletIDGetMethod,
    IsPluginInstalledGetMethod,
    SeqnoGetMethod,
)


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
    """Wallet v4 -- adds plugin support for subscriptions."""

    _data_model = WalletV4Data
    _config_model = WalletV4Config
    _params_model = WalletV4Params
    MAX_MESSAGES = 4

    async def _build_msg_cell(
        self,
        messages: list[WalletMessage],
        params: WalletV4Params | None = None,
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
        cell.store_uint(params.op_code, 8)

        for message in messages:
            cell.store_cell(message.serialize())

        return cell.end_cell()


class WalletV4R1(_WalletV4):
    """Wallet v4 Revision 1."""

    VERSION = ContractVersion.WalletV4R1


class WalletV4R2(_WalletV4):
    """Wallet v4 Revision 2."""

    VERSION = ContractVersion.WalletV4R2
