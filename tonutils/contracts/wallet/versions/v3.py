import typing as t

from pytoniq_core import (
    Cell,
    WalletMessage,
    begin_cell,
)

from ..base import BaseWallet
from ..get_methods import WalletGetMethods
from ....types import (
    PublicKey,
    WalletVersion,
    WalletV3Config,
    WalletV3Data,
    WalletV3Params,
)
from ....utils import calc_valid_until


class _WalletV3(
    BaseWallet[
        WalletV3Data,
        WalletV3Config,
        WalletV3Params,
    ],
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

    async def get_public_key(self) -> PublicKey:
        return await WalletGetMethods.get_public_key(
            client=self.client,
            address=self.address,
        )

    async def seqno(self) -> int:
        return await WalletGetMethods.seqno(
            client=self.client,
            address=self.address,
        )


class WalletV3R1(_WalletV3):
    VERSION = WalletVersion.WalletV3R1


class WalletV3R2(_WalletV3):
    VERSION = WalletVersion.WalletV3R2
