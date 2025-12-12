import typing as t

from pytoniq_core import Cell, WalletMessage, begin_cell

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
    """Wallet Preprocessed V2 contract."""

    _data_model = WalletPreprocessedV2Data
    """TlbScheme class for deserializing wallet state data."""

    _config_model = WalletPreprocessedV2Config
    """Configuration model class for this wallet version."""

    _params_model = WalletPreprocessedV2Params
    """Transaction parameters model class for this wallet version."""

    VERSION = ContractVersion.WalletPreprocessedV2
    """Contract version identifier."""

    MAX_MESSAGES = 255
    """Maximum number of messages allowed in a single transaction."""

    @classmethod
    def _build_out_actions(cls, messages: t.List[WalletMessage]) -> Cell:
        """
        Build out-actions list from wallet messages.

        :param messages: List of wallet messages to serialize
        :return: Cell containing serialized out-actions
        """
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
        """
        Build unsigned message cell for Wallet Preprocessed V2 transaction.

        :param messages: List of wallet messages (max 255)
        :param params: Optional wallet parameters (seqno, valid_until)
        :return: Unsigned message cell ready for signing
        """
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
        """
        Combine signature with unsigned message cell.

        :param signing_msg: Unsigned message cell
        :param signature: Ed25519 signature bytes
        :return: Signed message cell
        """
        cell = begin_cell()
        cell.store_bytes(signature)
        cell.store_ref(signing_msg)
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
