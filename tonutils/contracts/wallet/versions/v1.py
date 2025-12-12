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
    """Base implementation for Wallet V1 contracts."""

    _data_model = WalletV1Data
    """TlbScheme class for deserializing wallet state data."""

    _config_model = WalletV1Config
    """Configuration model class for this wallet version."""

    _params_model = WalletV1Params
    """Transaction parameters model class for this wallet version."""

    MAX_MESSAGES = 1
    """Maximum number of messages allowed in a single transaction."""

    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[WalletV1Params] = None,
    ) -> Cell:
        """
        Build unsigned message cell for Wallet V1 transaction.

        :param messages: List of wallet messages (max 1 for V1)
        :param params: Optional wallet parameters (seqno)
        :return: Unsigned message cell ready for signing
        """
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
        """
        Get public key from wallet state data.

        :return: Ed25519 public key instance stored in wallet
        """
        await self.refresh()
        return self.state_data.public_key

    async def seqno(self) -> int:
        """
        Get current sequence number from wallet state data.

        :return: Current sequence number
        """
        await self.refresh()
        return self.state_data.seqno


class WalletV1R1(_WalletV1):
    """Wallet V1 Revision 1 contract."""

    VERSION = ContractVersion.WalletV1R1
    """Contract version identifier."""


class WalletV1R2(_WalletV1, SeqnoGetMethod):
    """Wallet V1 Revision 2 contract."""

    VERSION = ContractVersion.WalletV1R2
    """Contract version identifier."""


class WalletV1R3(_WalletV1, SeqnoGetMethod, GetPublicKeyGetMethod):
    """Wallet V1 Revision 3 contract."""

    VERSION = ContractVersion.WalletV1R3
    """Contract version identifier."""
