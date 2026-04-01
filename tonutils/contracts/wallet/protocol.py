from __future__ import annotations

import typing as t

from ton_core import DEFAULT_SENDMODE, WorkchainID

from tonutils.contracts.protocol import ContractProtocol

if t.TYPE_CHECKING:
    from ton_core import AddressLike, Cell, PrivateKey, PublicKey, SendMode, StateInit, WalletMessage

    from tonutils.clients.protocol import ClientProtocol
    from tonutils.contracts.wallet.messages import (
        BaseMessageBuilder,
        ExternalMessage,
    )

_D = t.TypeVar("_D")
_C = t.TypeVar("_C")
_P = t.TypeVar("_P")

_TWallet = t.TypeVar("_TWallet")


@t.runtime_checkable
class WalletProtocol(ContractProtocol[_D], t.Protocol[_D, _C, _P]):
    """Structural protocol for TON wallet contract wrappers."""

    _data_model: type[_D]
    """TlbScheme-compatible class for wallet state data."""

    _config_model: type[_C]
    """Model class for wallet configuration."""

    _params_model: type[_P]
    """Model class for transaction parameters."""

    MAX_MESSAGES: t.ClassVar[int]
    """Maximum number of messages in a single transaction."""

    @property
    def config(self) -> _C:
        """Wallet configuration parameters."""

    @property
    def state_data(self) -> _D:
        """Decoded on-chain wallet state data."""

    @property
    def public_key(self) -> PublicKey | None:
        """Public key, or ``None``."""

    @property
    def private_key(self) -> PrivateKey | None:
        """Private key, or ``None`` for read-only wallets."""

    @classmethod
    def from_private_key(
        cls: type[_TWallet],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: _C | None = None,
    ) -> _TWallet:
        """Create wallet from a private key.

        :param client: TON client.
        :param private_key: Ed25519 private key.
        :param workchain: Target workchain.
        :param config: Wallet configuration, or ``None``.
        :return: New wallet instance.
        """

    @classmethod
    def from_mnemonic(
        cls: type[_TWallet],
        client: ClientProtocol,
        mnemonic: list[str] | str,
        validate: bool = True,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Any | None = None,
    ) -> tuple[_TWallet, PublicKey, PrivateKey, list[str]]:
        """Create wallet from a mnemonic phrase.

        :param client: TON client.
        :param mnemonic: BIP39 mnemonic (list or space-separated string).
        :param validate: Validate mnemonic checksum.
        :param workchain: Target workchain.
        :param config: Wallet configuration, or ``None``.
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list).
        """

    @classmethod
    def create(
        cls: type[_TWallet],
        client: ClientProtocol,
        mnemonic_length: int = 24,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Any | None = None,
    ) -> tuple[_TWallet, PublicKey, PrivateKey, list[str]]:
        """Create a new wallet with a random mnemonic.

        :param client: TON client.
        :param mnemonic_length: Word count (12, 18, or 24).
        :param workchain: Target workchain.
        :param config: Wallet configuration, or ``None``.
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list).
        """

    async def build_external_message(
        self,
        messages: t.Sequence[WalletMessage | BaseMessageBuilder],
        params: _P | None = None,
    ) -> ExternalMessage:
        """Build a signed external message.

        :param messages: Internal messages or message builders.
        :param params: Transaction parameters, or ``None``.
        :return: Signed ``ExternalMessage``.
        """

    async def batch_transfer_message(
        self: _TWallet,
        messages: t.Sequence[WalletMessage | BaseMessageBuilder],
        params: _P | None = None,
    ) -> ExternalMessage:
        """Build, sign, and send a batch transfer.

        :param messages: Internal messages or message builders.
        :param params: Transaction parameters, or ``None``.
        :return: Sent ``ExternalMessage``.
        """

    async def transfer_message(
        self: _TWallet,
        message: WalletMessage | BaseMessageBuilder,
        params: _P | None = None,
    ) -> ExternalMessage:
        """Build, sign, and send a single transfer.

        :param message: Internal message or message builder.
        :param params: Transaction parameters, or ``None``.
        :return: Sent ``ExternalMessage``.
        """

    async def transfer(
        self: _TWallet,
        destination: AddressLike,
        amount: int,
        body: Cell | str | None = None,
        state_init: StateInit | None = None,
        send_mode: SendMode | int = DEFAULT_SENDMODE,
        bounce: bool | None = None,
        params: _P | None = None,
    ) -> ExternalMessage:
        """Send a simple TON transfer.

        :param destination: Recipient address.
        :param amount: Amount in nanotons.
        :param body: Message body (``Cell`` or text comment), or ``None``.
        :param state_init: ``StateInit`` for deployment, or ``None``.
        :param send_mode: Send mode flags.
        :param bounce: Bounce on error, or ``None`` for auto-detect.
        :param params: Transaction parameters, or ``None``.
        :return: Sent ``ExternalMessage``.
        """
