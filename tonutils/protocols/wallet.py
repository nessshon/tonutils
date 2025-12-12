from __future__ import annotations

import typing as t

from pytoniq_core import Cell, StateInit, WalletMessage

from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.contract import ContractProtocol
from tonutils.types import (
    AddressLike,
    PublicKey,
    PrivateKey,
    SendMode,
    WorkchainID,
    DEFAULT_SENDMODE,
)

if t.TYPE_CHECKING:
    from tonutils.contracts.wallet.messages import (
        ExternalMessage,
        BaseMessageBuilder,
    )

_D = t.TypeVar("_D")
_C = t.TypeVar("_C")
_P = t.TypeVar("_P")

_TWallet = t.TypeVar("_TWallet")


@t.runtime_checkable
class WalletProtocol(ContractProtocol, t.Protocol[_D, _C, _P]):
    """Structural protocol for TON wallet contract wrappers."""

    _data_model: t.Type[_D]
    """TlbScheme-compatible class for wallet state data."""

    _config_model: t.Type[_C]
    """Model class for wallet configuration (subwallet_id, etc)."""

    _params_model: t.Type[_P]
    """Model class for transaction parameters (seqno, timeout, etc)."""

    MAX_MESSAGES: t.ClassVar[int]
    """Maximum number of messages allowed in a single transaction."""

    @property
    def config(self) -> _C:
        """Wallet configuration parameters."""

    @property
    def state_data(self) -> _D:
        """Decoded on-chain wallet state data."""

    @property
    def public_key(self) -> t.Optional[PublicKey]:
        """Public key associated with this wallet."""

    @property
    def private_key(self) -> t.Optional[PrivateKey]:
        """Private key for signing transactions."""

    @classmethod
    def from_private_key(
        cls: t.Type[_TWallet],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[_C] = None,
    ) -> _TWallet:
        """
        Create wallet instance from a private key.

        :param client: TON client for blockchain interactions
        :param private_key: Ed25519 PrivateKey instance
        :param workchain: Target workchain (default: BASECHAIN)
        :param config: Optional wallet configuration
        :return: New wallet instance
        """

    @classmethod
    def from_mnemonic(
        cls: t.Type[_TWallet],
        client: ClientProtocol,
        mnemonic: t.Union[t.List[str], str],
        validate: bool = True,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[t.Any] = None,
    ) -> t.Tuple[_TWallet, PublicKey, PrivateKey, t.List[str]]:
        """
        Create wallet instance from a mnemonic phrase.

        :param client: TON client for blockchain interactions
        :param mnemonic: BIP39 mnemonic phrase (list or space-separated string)
        :param validate: Whether to validate mnemonic checksum (default: True)
        :param workchain: Target workchain (default: BASECHAIN)
        :param config: Optional wallet configuration
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list)
        """

    @classmethod
    def create(
        cls: t.Type[_TWallet],
        client: ClientProtocol,
        mnemonic_length: int = 24,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[t.Any] = None,
    ) -> t.Tuple[_TWallet, PublicKey, PrivateKey, t.List[str]]:
        """
        Create a new wallet with a randomly generated mnemonic.

        :param client: TON client for blockchain interactions
        :param mnemonic_length: Number of words in mnemonic (12, 18, or 24; default: 24)
        :param workchain: Target workchain (default: BASECHAIN)
        :param config: Optional wallet configuration
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list)
        """

    async def build_external_message(
        self,
        messages: t.List[t.Union[WalletMessage, BaseMessageBuilder]],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """
        Build a signed external message for sending transactions.

        Constructs a signed external message but does not send it.

        :param messages: List of internal messages or message builders
        :param params: Optional transaction parameters (seqno, timeout, etc.)
        :return: Signed external message ready for sending
        """

    async def batch_transfer_message(
        self: _TWallet,
        messages: t.List[t.Union[WalletMessage, BaseMessageBuilder]],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """
        Build and send a batch transfer message with multiple recipients.

        :param messages: List of internal messages or message builders
        :param params: Optional transaction parameters
        :return: Signed external message that was sent
        """

    async def transfer_message(
        self: _TWallet,
        message: t.Union[WalletMessage, BaseMessageBuilder],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """
        Build and send a transfer message for a single recipient.

        :param message: Internal message or message builder
        :param params: Optional transaction parameters
        :return: Signed external message that was sent
        """

    async def transfer(
        self: _TWallet,
        destination: AddressLike,
        amount: int,
        body: t.Optional[t.Union[Cell, str]] = None,
        state_init: t.Optional[StateInit] = None,
        send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE,
        bounce: t.Optional[bool] = None,
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """
        Build and send a transfer to a single destination.

        :param destination: Recipient address (Address, string, or domain)
        :param amount: Amount to send in nanotons
        :param body: Optional message body (Cell or text comment)
        :param state_init: Optional StateInit for contract deployment
        :param send_mode: Message send mode (default: pay fees separately)
        :param bounce: Whether message should bounce on error (default: auto)
        :param params: Optional transaction parameters
        :return: Signed external message that was sent
        """
