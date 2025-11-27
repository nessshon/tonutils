from __future__ import annotations

import typing as t

from pytoniq_core import Cell, WalletMessage, begin_cell

from tonutils.contracts.versions import ContractVersion
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.configs import WalletV2Config
from tonutils.contracts.wallet.methods import SeqnoGetMethod, GetPublicKeyGetMethod
from tonutils.contracts.wallet.params import WalletV2Params
from tonutils.contracts.wallet.tlb import WalletV2Data
from tonutils.utils import calc_valid_until


class _WalletV2(
    BaseWallet[
        WalletV2Data,
        WalletV2Config,
        WalletV2Params,
    ],
    SeqnoGetMethod,
    GetPublicKeyGetMethod,
):
    _data_model = WalletV2Data
    _config_model = WalletV2Config
    _params_model = WalletV2Params

    MAX_MESSAGES = 4

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV2Params] = None,
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
        cell.store_uint(seqno, 32)
        cell.store_uint(valid_until, 32)

        for message in messages:
            cell.store_cell(message.serialize())

        return cell.end_cell()


class WalletV2R1(_WalletV2):
    VERSION = ContractVersion.WalletV2R1


class WalletV2R2(_WalletV2):
    VERSION = ContractVersion.WalletV2R2
