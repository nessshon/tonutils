import typing as t

from pytoniq_core import (
    Cell,
    WalletMessage,
    begin_cell,
    Address,
)

from ..base import BaseWallet
from ..get_methods import WalletGetMethods
from ....types import (
    AddressLike,
    PublicKey,
    WalletVersion,
    WalletV4Config,
    WalletV4Data,
    WalletV4Params,
)
from ....utils import calc_valid_until


class _WalletV4(
    BaseWallet[
        WalletV4Data,
        WalletV4Config,
        WalletV4Params,
    ],
):
    _config_model = WalletV4Config
    _data_model = WalletV4Data
    _params_model = WalletV4Params

    MAX_MESSAGES = 4

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV4Params] = None,
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
        cell.store_uint(params.op_code, 8)

        for message in messages:
            cell.store_cell(message.serialize())

        return cell.end_cell()

    async def get_public_key(self) -> PublicKey:
        return await WalletGetMethods.get_public_key(
            client=self.client,
            address=self.address,
        )

    async def get_subwallet_id(self) -> int:
        return await WalletGetMethods.get_subwallet_id(
            client=self.client,
            address=self.address,
        )

    async def seqno(self) -> int:
        return await WalletGetMethods.seqno(
            client=self.client,
            address=self.address,
        )

    async def get_plugin_list(self) -> t.List[Address]:
        return await WalletGetMethods.get_plugin_list(
            client=self.client,
            address=self.address,
        )

    async def is_plugin_installed(self, plugin_address: AddressLike) -> bool:
        return await WalletGetMethods.is_plugin_installed(
            client=self.client,
            address=self.address,
            plugin_address=plugin_address,
        )


class WalletV4R1(_WalletV4):
    VERSION = WalletVersion.WalletV4R1


class WalletV4R2(_WalletV4):
    VERSION = WalletVersion.WalletV4R2
