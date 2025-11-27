import typing as t

from pytoniq_core import (
    Cell,
    WalletMessage,
    begin_cell,
)

from tonutils.contracts.versions import ContractVersion
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.configs import WalletPreprocessedV2Config
from tonutils.contracts.wallet.params import WalletPreprocessedV2Params
from tonutils.contracts.wallet.tlb import OutActionSendMsg, WalletPreprocessedV2Data
from tonutils.types import PublicKey
from tonutils.utils import calc_valid_until


class WalletPreprocessedV2(
    BaseWallet[
        WalletPreprocessedV2Data,
        WalletPreprocessedV2Config,
        WalletPreprocessedV2Params,
    ]
):
    _data_model = WalletPreprocessedV2Data
    _config_model = WalletPreprocessedV2Config
    _params_model = WalletPreprocessedV2Params

    VERSION = ContractVersion.WalletPreprocessedV2
    MAX_MESSAGES = 255

    @classmethod
    def _build_out_actions(cls, messages: t.List[WalletMessage]) -> Cell:
        actions_cell = Cell.empty()

        for msg in messages:
            action = OutActionSendMsg(msg)
            action_cell = begin_cell()
            action_cell.store_ref(actions_cell)
            action_cell.store_cell(action.serialize())
            actions_cell = action_cell.end_cell()

        return actions_cell

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletPreprocessedV2Params] = None,
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
        cell.store_uint(valid_until, 64)
        cell.store_uint(seqno, 16)
        cell.store_ref(self._build_out_actions(messages))
        return cell.end_cell()

    async def _build_sign_msg_cell(
        self,
        signing_msg: Cell,
        signature: bytes,
    ) -> Cell:
        cell = begin_cell()
        cell.store_bytes(signature)
        cell.store_ref(signing_msg)
        return cell.end_cell()

    async def get_public_key(self) -> PublicKey:
        await self.refresh()
        return self.state_data.public_key

    async def seqno(self) -> int:
        await self.refresh()
        return self.state_data.seqno
