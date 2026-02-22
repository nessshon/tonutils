from __future__ import annotations

import abc
import typing as t

from pytoniq_core import Address, Cell, StateInit, WalletMessage, begin_cell
from pytoniq_core.crypto.keys import mnemonic_new, mnemonic_to_private_key, words
from pytoniq_core.crypto.signature import sign_message

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.base import BaseContract
from tonutils.contracts.codes import CONTRACT_CODES
from tonutils.contracts.wallet.configs import BaseWalletConfig
from tonutils.contracts.wallet.messages import (
    BaseMessageBuilder,
    ExternalMessage,
    TONTransferBuilder,
)
from tonutils.contracts.wallet.params import BaseWalletParams
from tonutils.contracts.wallet.protocol import WalletProtocol
from tonutils.contracts.wallet.tlb import BaseWalletData
from tonutils.exceptions import ContractError
from tonutils.types import (
    AddressLike,
    ContractInfo,
    SendMode,
    PublicKey,
    PrivateKey,
    WorkchainID,
    DEFAULT_SENDMODE,
)
from tonutils.utils import to_cell

_D = t.TypeVar("_D", bound=BaseWalletData)
_C = t.TypeVar("_C", bound=BaseWalletConfig)
_P = t.TypeVar("_P", bound=BaseWalletParams)

_TWallet = t.TypeVar("_TWallet", bound="BaseWallet[t.Any, t.Any, t.Any]")

VALID_MNEMONIC_LENGTHS: t.Final[t.Tuple[int, ...]] = (12, 18, 24)
"""Valid mnemonic phrase lengths in words."""


class BaseWallet(BaseContract, WalletProtocol[_D, _C, _P], abc.ABC):
    """Base implementation for TON wallet contracts."""

    _data_model: t.Type[_D]
    """TlbScheme class for deserializing wallet state data."""

    _config_model: t.Type[_C]
    """Configuration model class for this wallet version."""

    _params_model: t.Type[_P]
    """Transaction parameters model class for this wallet version."""

    MAX_MESSAGES: t.ClassVar[int]
    """Maximum number of messages allowed in a single transaction."""

    def __init__(
        self,
        client: ClientProtocol,
        address: Address,
        state_init: t.Optional[StateInit] = None,
        info: t.Optional[ContractInfo] = None,
        config: t.Optional[_C] = None,
        private_key: t.Optional[PrivateKey] = None,
    ) -> None:
        """
        :param client: TON client.
        :param address: Wallet address.
        :param state_init: Code and data, or `None`.
        :param info: Preloaded contract state, or `None`.
        :param config: Wallet configuration, or `None`.
        :param private_key: Signing key, or `None` for read-only.
        """
        self._config = config
        self._private_key: t.Optional[PrivateKey] = None
        self._public_key: t.Optional[PublicKey] = None

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
        return t.cast(_C, self._config)

    @property
    def public_key(self) -> t.Optional[PublicKey]:
        """Public key, or `None`."""
        return self._public_key if self._public_key else None

    @property
    def private_key(self) -> t.Optional[PrivateKey]:
        """Private key, or `None` for read-only wallets."""
        return self._private_key if self._private_key else None

    @abc.abstractmethod
    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[_P] = None,
    ) -> Cell:
        """Build unsigned message cell for this wallet version.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or `None`.
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
        messages: t.List[WalletMessage],
        params: t.Optional[_P] = None,
    ) -> Cell:
        """Build and sign a message cell.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or `None`.
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
        signature = sign_message(signed_msg.hash, self._private_key.keypair.as_bytes)
        return await self._build_sign_msg_cell(signed_msg, signature)

    @classmethod
    def from_private_key(
        cls: t.Type[_TWallet],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[_C] = None,
    ) -> _TWallet:
        """Create wallet from a private key.

        :param client: TON client.
        :param private_key: Ed25519 private key.
        :param workchain: Target workchain.
        :param config: Wallet configuration, or `None`.
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
        cls: t.Type[_TWallet],
        client: ClientProtocol,
        mnemonic: t.Union[t.List[str], str],
        validate: bool = True,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[_C] = None,
    ) -> t.Tuple[_TWallet, PublicKey, PrivateKey, t.List[str]]:
        """Create wallet from a mnemonic phrase.

        :param client: TON client.
        :param mnemonic: BIP39 mnemonic (list or space-separated string).
        :param validate: Validate mnemonic checksum.
        :param workchain: Target workchain.
        :param config: Wallet configuration, or `None`.
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
        cls: t.Type[_TWallet],
        client: ClientProtocol,
        mnemonic_length: int = 24,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[_C] = None,
    ) -> t.Tuple[_TWallet, PublicKey, PrivateKey, t.List[str]]:
        """Create a new wallet with a random mnemonic.

        :param client: TON client.
        :param mnemonic_length: Word count (12, 18, or 24).
        :param workchain: Target workchain.
        :param config: Wallet configuration, or `None`.
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list).
        :raises ContractError: If mnemonic length is invalid.
        """
        cls._validate_mnemonic_length(mnemonic_length)

        mnemonic = mnemonic_new(mnemonic_length)
        return cls.from_mnemonic(client, mnemonic, True, workchain, config)

    async def build_external_message(
        self,
        messages: t.List[t.Union[WalletMessage, BaseMessageBuilder]],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """Build a signed external message.

        :param messages: Internal messages or message builders.
        :param params: Transaction parameters, or `None`.
        :return: Signed `ExternalMessage`.
        """
        messages = [
            (
                message
                if isinstance(message, WalletMessage)
                else await message.build(self)
            )
            for message in messages
        ]
        await self.refresh()
        self._validate_message_count(messages)
        self._validate_params_type(params)
        body = await self._build_signed_msg_cell(messages, params)
        state_init = self.state_init if not self.is_active else None
        return ExternalMessage(dest=self.address, body=body, state_init=state_init)

    async def batch_transfer_message(
        self,
        messages: t.List[t.Union[WalletMessage, BaseMessageBuilder]],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """Build, sign, and send a batch transfer.

        :param messages: Internal messages or message builders.
        :param params: Transaction parameters, or `None`.
        :return: Sent `ExternalMessage`.
        """
        external_msg = await self.build_external_message(messages, params)
        await self.client.send_message(external_msg.as_hex)
        return external_msg

    async def transfer_message(
        self,
        message: t.Union[WalletMessage, BaseMessageBuilder],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """Build, sign, and send a single transfer.

        :param message: Internal message or message builder.
        :param params: Transaction parameters, or `None`.
        :return: Sent `ExternalMessage`.
        """
        return await self.batch_transfer_message([message], params)

    async def transfer(
        self,
        destination: AddressLike,
        amount: int,
        body: t.Optional[t.Union[Cell, str]] = None,
        state_init: t.Optional[StateInit] = None,
        send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE,
        bounce: t.Optional[bool] = None,
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """Send a simple TON transfer.

        :param destination: Recipient address.
        :param amount: Amount in nanotons.
        :param body: Message body (`Cell` or text comment), or `None`.
        :param state_init: `StateInit` for deployment, or `None`.
        :param send_mode: Send mode flags.
        :param bounce: Bounce on error, or `None` for auto-detect.
        :param params: Transaction parameters, or `None`.
        :return: Sent `ExternalMessage`.
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
        cls: t.Type[_TWallet],
        config: _C,
    ) -> None:
        """Validate config type for this wallet version.

        :param config: Configuration to validate.
        :raises ContractError: If type does not match `_config_model`.
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
        cls: t.Type[_TWallet],
        params: t.Optional[_P] = None,
    ) -> None:
        """Validate params type for this wallet version.

        :param params: Parameters to validate, or `None`.
        :raises ContractError: If type does not match `_params_model`.
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
        cls: t.Type[_TWallet],
        messages: t.List[WalletMessage],
    ) -> None:
        """Validate message count against `MAX_MESSAGES`.

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
        cls: t.Type[_TWallet],
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
    def validate_mnemonic(cls, mnemonic: t.Union[str, t.List[str]]) -> None:
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
