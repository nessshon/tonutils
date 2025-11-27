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
    _data_model = WalletV3Data
    _config_model = WalletV3Config
    _params_model = WalletV3Params

    MAX_MESSAGES = 4

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV3Params] = None,
    ) -> Cell:
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
    VERSION = ContractVersion.WalletV3R1


class WalletV3R2(_WalletV3):
    VERSION = ContractVersion.WalletV3R2
