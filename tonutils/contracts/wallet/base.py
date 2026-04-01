from __future__ import annotations

import abc
import typing as t

from ton_core import (
    CONTRACT_CODES,
    DEFAULT_SENDMODE,
    Address,
    AddressLike,
    BaseWalletConfig,
    BaseWalletData,
    BaseWalletParams,
    Cell,
    PrivateKey,
    PublicKey,
    SendMode,
    SignatureDomain,
    StateInit,
    WalletMessage,
    WorkchainID,
    begin_cell,
    mnemonic_new,
    mnemonic_to_private_key,
    sign_message,
    to_cell,
    words,
)

from tonutils.contracts.base import BaseContract
from tonutils.contracts.wallet.messages import (
    BaseMessageBuilder,
    ExternalMessage,
    TONTransferBuilder,
)
from tonutils.contracts.wallet.protocol import WalletProtocol
from tonutils.exceptions import ContractError

if t.TYPE_CHECKING:
    from tonutils.clients.protocol import ClientProtocol
    from tonutils.types import ContractInfo

_D = t.TypeVar("_D", bound=BaseWalletData)
_C = t.TypeVar("_C", bound=BaseWalletConfig)
_P = t.TypeVar("_P", bound=BaseWalletParams)

_TWallet = t.TypeVar("_TWallet", bound="BaseWallet[t.Any, t.Any, t.Any]")

VALID_MNEMONIC_LENGTHS: t.Final[tuple[int, ...]] = (12, 18, 24)
"""Valid mnemonic phrase lengths in words."""


class BaseWallet(BaseContract[_D], WalletProtocol[_D, _C, _P], abc.ABC):
    """Base implementation for TON wallet contracts."""

    _data_model: type[_D]
    """TlbScheme class for deserializing wallet state data."""

    _config_model: type[_C]
    """Configuration model class for this wallet version."""

    _params_model: type[_P]
    """Transaction parameters model class for this wallet version."""

    MAX_MESSAGES: t.ClassVar[int]
    """Maximum number of messages allowed in a single transaction."""

    def __init__(
        self,
        client: ClientProtocol,
        address: Address,
        state_init: StateInit | None = None,
        info: ContractInfo | None = None,
        config: _C | None = None,
        private_key: PrivateKey | None = None,
    ) -> None:
        """Initialize the wallet.

        :param client: TON client.
        :param address: Wallet address.
        :param state_init: Code and data, or ``None``.
        :param info: Preloaded contract state, or ``None``.
        :param config: Wallet configuration, or ``None``.
        :param private_key: Signing key, or ``None`` for read-only.
        """
        self._config = config
        self._private_key: PrivateKey | None = None
        self._public_key: PublicKey | None = None

        if private_key is not None:
            self._private_key = private_key
            self._public_key = private_key.public_key
        super().__init__(client, address, state_init, info)

    @property
    def state_data(self) -> _D:
        """Decoded on-chain wallet state data."""
        return super().state_data

    @property
    def config(self) -> _C:
        """Wallet configuration parameters."""
        return t.cast("_C", self._config)

    @property
    def public_key(self) -> PublicKey | None:
        """Public key, or ``None``."""
        return self._public_key if self._public_key else None

    @property
    def private_key(self) -> PrivateKey | None:
        """Private key, or ``None`` for read-only wallets."""
        return self._private_key if self._private_key else None

    @abc.abstractmethod
    async def _build_msg_cell(
        self,
        messages: list[WalletMessage],
        params: _P | None = None,
    ) -> Cell:
        """Build unsigned message cell for this wallet version.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or ``None``.
        :return: Unsigned message cell.
        """

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
        cell.store_cell(signing_msg)
        return cell.end_cell()

    async def _build_signed_msg_cell(
        self,
        messages: list[WalletMessage],
        params: _P | None = None,
    ) -> Cell:
        """Build and sign a message cell.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or ``None``.
        :return: Signed message cell.
        :raises ContractError: If private key is not set.
        """
        if self._private_key is None:
            raise ContractError(
                self,
                f"Cannot sign message: "
                f"`private_key` is not set for wallet `{self.VERSION!r}`.",
            )

        signed_msg = await self._build_msg_cell(messages, params)
        domain = SignatureDomain(self.client.network)
        data = domain.data_to_sign(signed_msg.hash)
        signature = sign_message(data, self._private_key.keypair.as_bytes)
        return await self._build_sign_msg_cell(signed_msg, signature)

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
        config = config or cls._config_model()
        cls._validate_config_type(config)
        config.public_key = private_key.public_key

        code = to_cell(CONTRACT_CODES[cls.VERSION])
        data = cls._data_model(**config.to_dict()).serialize()

        state_init = StateInit(code=code, data=data)
        address = Address((workchain.value, state_init.serialize().hash))
        return cls(client, address, state_init, None, config, private_key)

    @classmethod
    def from_mnemonic(
        cls: type[_TWallet],
        client: ClientProtocol,
        mnemonic: list[str] | str,
        validate: bool = True,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: _C | None = None,
    ) -> tuple[_TWallet, PublicKey, PrivateKey, list[str]]:
        """Create wallet from a mnemonic phrase.

        :param client: TON client.
        :param mnemonic: BIP39 mnemonic (list or space-separated string).
        :param validate: Validate mnemonic checksum.
        :param workchain: Target workchain.
        :param config: Wallet configuration, or ``None``.
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list).
        """
        if isinstance(mnemonic, str):
            mnemonic = mnemonic.strip().lower().split()
        if validate:
            cls.validate_mnemonic(mnemonic)

        pub_key_bytes, priv_key_bytes = mnemonic_to_private_key(mnemonic)
        private_key = PrivateKey(priv_key_bytes)
        public_key = PublicKey(pub_key_bytes)

        wallet = cls.from_private_key(client, private_key, workchain, config)
        return wallet, public_key, private_key, mnemonic

    @classmethod
    def create(
        cls: type[_TWallet],
        client: ClientProtocol,
        mnemonic_length: int = 24,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: _C | None = None,
    ) -> tuple[_TWallet, PublicKey, PrivateKey, list[str]]:
        """Create a new wallet with a random mnemonic.

        :param client: TON client.
        :param mnemonic_length: Word count (12, 18, or 24).
        :param workchain: Target workchain.
        :param config: Wallet configuration, or ``None``.
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list).
        :raises ContractError: If mnemonic length is invalid.
        """
        cls._validate_mnemonic_length(mnemonic_length)

        mnemonic = mnemonic_new(mnemonic_length)
        return cls.from_mnemonic(client, mnemonic, True, workchain, config)

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
        resolved: list[WalletMessage] = [
            (
                message
                if isinstance(message, WalletMessage)
                else await message.build(self)
            )
            for message in messages
        ]
        await self.refresh()
        self._validate_message_count(resolved)
        self._validate_params_type(params)
        body = await self._build_signed_msg_cell(resolved, params)
        state_init = self.state_init if not self.is_active else None
        return ExternalMessage(dest=self.address, body=body, state_init=state_init)

    async def batch_transfer_message(
        self,
        messages: t.Sequence[WalletMessage | BaseMessageBuilder],
        params: _P | None = None,
    ) -> ExternalMessage:
        """Build, sign, and send a batch transfer.

        :param messages: Internal messages or message builders.
        :param params: Transaction parameters, or ``None``.
        :return: Sent ``ExternalMessage``.
        """
        external_msg = await self.build_external_message(messages, params)
        await self.client.send_message(external_msg.as_hex)
        return external_msg

    async def transfer_message(
        self,
        message: WalletMessage | BaseMessageBuilder,
        params: _P | None = None,
    ) -> ExternalMessage:
        """Build, sign, and send a single transfer.

        :param message: Internal message or message builder.
        :param params: Transaction parameters, or ``None``.
        :return: Sent ``ExternalMessage``.
        """
        return await self.batch_transfer_message([message], params)

    async def transfer(
        self,
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
        message = TONTransferBuilder(
            destination=destination,
            amount=amount,
            body=body,
            state_init=state_init,
            send_mode=send_mode,
            bounce=bounce,
        )
        return await self.transfer_message(message, params)

    @classmethod
    def _validate_config_type(
        cls: type[_TWallet],
        config: _C,
    ) -> None:
        """Validate config type for this wallet version.

        :param config: Configuration to validate.
        :raises ContractError: If type does not match ``_config_model``.
        """
        if not isinstance(config, cls._config_model):
            raise ContractError(
                cls,
                f"Invalid contract config type for `{cls.VERSION!r}`. "
                f"Expected {cls._config_model.__name__}, "
                f"got {type(config).__name__}.",
            )

    @classmethod
    def _validate_params_type(
        cls: type[_TWallet],
        params: _P | None = None,
    ) -> None:
        """Validate params type for this wallet version.

        :param params: Parameters to validate, or ``None``.
        :raises ContractError: If type does not match ``_params_model``.
        """
        if params is not None and not isinstance(params, cls._params_model):
            raise ContractError(
                cls,
                f"Invalid params type for `{cls.VERSION!r}`. "
                f"Expected {cls._params_model.__name__}, "
                f"got {type(params).__name__ if params is not None else 'None'}.",
            )

    @classmethod
    def _validate_message_count(
        cls: type[_TWallet],
        messages: list[WalletMessage],
    ) -> None:
        """Validate message count against ``MAX_MESSAGES``.

        :param messages: Messages to validate.
        :raises ContractError: If count exceeds the limit.
        """
        if len(messages) > cls.MAX_MESSAGES:
            raise ContractError(
                cls.__name__,
                f"For `{cls.VERSION!r}`, "
                f"maximum messages amount is {cls.MAX_MESSAGES}, "
                f"but got {len(messages)}.",
            )

    @classmethod
    def _validate_mnemonic_length(
        cls: type[_TWallet],
        mnemonic_length: int,
    ) -> None:
        """Validate mnemonic word count.

        :param mnemonic_length: Number of words.
        :raises ContractError: If not in (12, 18, 24).
        """
        if mnemonic_length not in VALID_MNEMONIC_LENGTHS:
            raise ContractError(
                cls,
                f"Invalid mnemonic length: {mnemonic_length}. "
                f"Expected one of {VALID_MNEMONIC_LENGTHS}.",
            )

    @classmethod
    def validate_mnemonic(cls, mnemonic: str | list[str]) -> None:
        """Validate mnemonic phrase.

        :param mnemonic: Mnemonic (list or space-separated string).
        :raises ValueError: If length is invalid or words are not in the wordlist.
        """
        if isinstance(mnemonic, str):
            mnemonic_words = mnemonic.strip().lower().split()
        else:
            mnemonic_words = [w.strip().lower() for w in mnemonic]
        if len(mnemonic_words) not in VALID_MNEMONIC_LENGTHS:
            raise ValueError(
                f"Invalid mnemonic length: {len(mnemonic_words)}. "
                f"Expected one of {sorted(VALID_MNEMONIC_LENGTHS)}."
            )

        invalid = [(i + 1, w) for i, w in enumerate(mnemonic_words) if w not in words]
        if invalid:
            formatted = ", ".join(f"{idx}. {word}" for idx, word in invalid)
            raise ValueError(f"Invalid mnemonic word(s): {formatted}")
