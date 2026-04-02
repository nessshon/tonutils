from ton_core import (
    Cell,
    ContractVersion,
    OutActionSendMsg,
    PublicKey,
    WalletMessage,
    WalletPreprocessedV2Config,
    WalletPreprocessedV2Data,
    WalletPreprocessedV2Params,
    begin_cell,
    calc_valid_until,
)

from tonutils.contracts.wallet.base import BaseWallet


class WalletPreprocessedV2(
    BaseWallet[
        WalletPreprocessedV2Data,
        WalletPreprocessedV2Config,
        WalletPreprocessedV2Params,
    ]
):
    """Preprocessed Wallet v2 -- stores out-actions as a ref, up to 255 messages."""

    _data_model = WalletPreprocessedV2Data
    _config_model = WalletPreprocessedV2Config
    _params_model = WalletPreprocessedV2Params
    VERSION = ContractVersion.WalletPreprocessedV2
    MAX_MESSAGES = 255

    @classmethod
    def _build_out_actions(cls, messages: list[WalletMessage]) -> Cell:
        """Build out-actions list from wallet messages.

        :param messages: Wallet messages to serialize.
        :return: Out-actions ``Cell``.
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
        messages: list[WalletMessage],
        params: WalletPreprocessedV2Params | None = None,
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
        cell.store_uint(valid_until, 64)
        cell.store_uint(seqno, 16)
        cell.store_ref(self._build_out_actions(messages))
        return cell.end_cell()

    async def _build_sign_msg_cell(
        self,
        signing_msg: Cell,
        signature: bytes,
    ) -> Cell:
        """Combine signature with unsigned message cell.

        :param signing_msg: Unsigned message cell.
        :param signature: Ed25519 signature bytes.
        :return: Signed message cell.
        """
        cell = begin_cell()
        cell.store_bytes(signature)
        cell.store_ref(signing_msg)
        return cell.end_cell()

    async def get_public_key(self) -> PublicKey:
        """Return Ed25519 public key from wallet state data."""
        await self.refresh()
        return self.state_data.public_key

    async def seqno(self) -> int:
        """Return current sequence number from wallet state data."""
        await self.refresh()
        return self.state_data.seqno
