from __future__ import annotations

import typing as t

from pytoniq_core import Cell, WalletMessage, begin_cell

from tonutils.contracts.versions import ContractVersion
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.configs import WalletV1Config
from tonutils.contracts.wallet.methods import SeqnoGetMethod, GetPublicKeyGetMethod
from tonutils.contracts.wallet.params import WalletV1Params
from tonutils.contracts.wallet.tlb import WalletV1Data
from tonutils.types import PublicKey


class _WalletV1(
    BaseWallet[
        WalletV1Data,
        WalletV1Config,
        WalletV1Params,
    ]
):
    _data_model = WalletV1Data
    _config_model = WalletV1Config
    _params_model = WalletV1Params

    MAX_MESSAGES = 1

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV1Params] = None,
    ) -> Cell:
        params = params or self._params_model()

        seqno = (
            params.seqno
            if params.seqno is not None
            else self.state_data.seqno if self.is_active else 0
        )

        cell = begin_cell()
        cell.store_uint(seqno, 32)

        for message in messages:
            cell.store_cell(message.serialize())

        return cell.end_cell()

    async def get_public_key(self) -> PublicKey:
        await self.refresh()
        return self.state_data.public_key

    async def seqno(self) -> int:
        await self.refresh()
        return self.state_data.seqno


class WalletV1R1(_WalletV1):
    VERSION = ContractVersion.WalletV1R1


class WalletV1R2(_WalletV1, SeqnoGetMethod):
    VERSION = ContractVersion.WalletV1R2


class WalletV1R3(_WalletV1, SeqnoGetMethod, GetPublicKeyGetMethod):
    VERSION = ContractVersion.WalletV1R3
