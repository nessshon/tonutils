from __future__ import annotations

import abc
import typing as t

from pytoniq_core import Address, Cell, StateInit, WalletMessage, begin_cell
from pytoniq_core.crypto.keys import mnemonic_new, mnemonic_to_private_key, words
from pytoniq_core.crypto.signature import sign_message

from tonutils.contracts.base import BaseContract
from tonutils.contracts.codes import CONTRACT_CODES
from tonutils.contracts.wallet.configs import BaseWalletConfig
from tonutils.contracts.wallet.messages import (
    BaseMessageBuilder,
    ExternalMessage,
    TONTransferBuilder,
)
from tonutils.contracts.wallet.params import BaseWalletParams
from tonutils.contracts.wallet.tlb import BaseWalletData
from tonutils.exceptions import ContractError
from tonutils.protocols.client import ClientProtocol
from tonutils.protocols.wallet import WalletProtocol
from tonutils.types import (
    AddressLike,
    ContractStateInfo,
    SendMode,
    PublicKey,
    PrivateKey,
    WorkchainID,
    DEFAULT_SENDMODE,
)
from tonutils.utils import resolve_wallet_address, to_cell

_D = t.TypeVar("_D", bound=BaseWalletData)
_C = t.TypeVar("_C", bound=BaseWalletConfig)
_P = t.TypeVar("_P", bound=BaseWalletParams)

_TWallet = t.TypeVar("_TWallet", bound="BaseWallet[t.Any, t.Any, t.Any]")

VALID_MNEMONIC_LENGTHS: t.Final[t.Tuple[int, ...]] = (12, 18, 24)
"""Valid BIP39 mnemonic phrase lengths in words."""


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
        state_info: t.Optional[ContractStateInfo] = None,
        config: t.Optional[_C] = None,
        private_key: t.Optional[PrivateKey] = None,
    ) -> None:
        """
        Initialize wallet instance.

        :param client: TON client for blockchain interactions
        :param address: Wallet address on the blockchain
        :param state_init: Optional StateInit (code and data)
        :param state_info: Optional preloaded contract state
        :param config: Optional wallet configuration
        :param private_key: Optional private key for signing transactions
        """
        self._config = config
        self._private_key: t.Optional[PrivateKey] = None
        self._public_key: t.Optional[PublicKey] = None

        if private_key is not None:
            self._private_key = private_key
            self._public_key = private_key.public_key
        super().__init__(client, address, state_init, state_info)

    @property
    def state_data(self) -> _D:
        """
        Decoded on-chain wallet state data.

        :return: Typed wallet data
        """
        return super().state_data

    @property
    def config(self) -> _C:
        """
        Wallet configuration parameters.

        :return: Configuration object
        """
        return t.cast(_C, self._config)

    @property
    def public_key(self) -> t.Optional[PublicKey]:
        """
        Public key associated with this wallet.

        :return: Public key or None if not available
        """
        return self._public_key if self._public_key else None

    @property
    def private_key(self) -> t.Optional[PrivateKey]:
        """
        Private key for signing transactions.

        :return: Private key or None if wallet is read-only
        """
        return self._private_key if self._private_key else None

    @abc.abstractmethod
    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[_P] = None,
    ) -> Cell:
        """
        Build unsigned message cell for this wallet version.

        :param messages: List of internal messages to include
        :param params: Optional transaction parameters
        :return: Unsigned message cell ready for signing
        """

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
        cell.store_cell(signing_msg)
        return cell.end_cell()

    async def _build_signed_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[_P] = None,
    ) -> Cell:
        """
        Build and sign message cell.

        :param messages: List of internal messages to include
        :param params: Optional transaction parameters
        :return: Fully signed message cell
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
        """
        Create wallet instance from a private key.

        :param client: TON client for blockchain interactions
        :param private_key: Ed25519 PrivateKey instance
        :param workchain: Target workchain (default: BASECHAIN)
        :param config: Optional wallet configuration
        :return: New wallet instance
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
        """
        Create wallet instance from a mnemonic phrase.

        :param client: TON client for blockchain interactions
        :param mnemonic: BIP39 mnemonic phrase (list or space-separated string)
        :param validate: Whether to validate mnemonic checksum (default: True)
        :param workchain: Target workchain (default: BASECHAIN)
        :param config: Optional wallet configuration
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list)
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
        """
        Create a new wallet with a randomly generated mnemonic.

        :param client: TON client for blockchain interactions
        :param mnemonic_length: Number of words in mnemonic (12, 18, or 24; default: 24)
        :param workchain: Target workchain (default: BASECHAIN)
        :param config: Optional wallet configuration
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list)
        """
        cls._validate_mnemonic_length(mnemonic_length)

        mnemonic = mnemonic_new(mnemonic_length)
        return cls.from_mnemonic(client, mnemonic, True, workchain, config)

    async def build_external_message(
        self,
        messages: t.List[t.Union[WalletMessage, BaseMessageBuilder]],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """
        Build a signed external message for sending transactions.

        :param messages: List of internal messages or message builders
        :param params: Optional transaction parameters (seqno, timeout, etc.)
        :return: Signed external message ready for sending
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
        """
        Build and send a batch transfer message with multiple recipients.

        :param messages: List of internal messages or message builders
        :param params: Optional transaction parameters
        :return: Signed external message that was sent
        """
        external_msg = await self.build_external_message(messages, params)
        await self.client.send_boc(external_msg.as_hex)
        return external_msg

    async def transfer_message(
        self,
        message: t.Union[WalletMessage, BaseMessageBuilder],
        params: t.Optional[_P] = None,
    ) -> ExternalMessage:
        """
        Build and send a transfer message for a single recipient.

        :param message: Internal message or message builder
        :param params: Optional transaction parameters
        :return: Signed external message that was sent
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
        destination = await resolve_wallet_address(self.client, destination)
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
        """
        Validate that config matches expected type for this wallet version.

        :param config: Configuration object to validate
        :raises ContractError: If config type is incorrect
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
        """
        Validate that params match expected type for this wallet version.

        :param params: Parameters object to validate
        :raises ContractError: If params type is incorrect
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
        """
        Validate that message count does not exceed MAX_MESSAGES limit.

        :param messages: List of messages to validate
        :raises ContractError: If too many messages
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
        """
        Validate that mnemonic length is valid (12, 18, or 24 words).

        :param mnemonic_length: Number of words to validate
        :raises ContractError: If length is invalid
        """
        if mnemonic_length not in VALID_MNEMONIC_LENGTHS:
            raise ContractError(
                cls,
                f"Invalid mnemonic length: {mnemonic_length}. "
                f"Expected one of {VALID_MNEMONIC_LENGTHS}.",
            )

    @classmethod
    def validate_mnemonic(cls, mnemonic: t.Union[str, t.List[str]]) -> None:
        """
        Validate BIP39 mnemonic phrase.

        Checks that mnemonic has valid length and all words exist in BIP39 wordlist.

        :param mnemonic: Mnemonic phrase (list or space-separated string)
        :raises ValueError: If mnemonic length is invalid or contains invalid words
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
