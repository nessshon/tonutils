from __future__ import annotations

import abc
import typing as t

from pytoniq_core import (
    Cell,
    WalletMessage,
    StateInit,
    begin_cell,
    Address,
)
from pytoniq_core.crypto.keys import (
    mnemonic_to_private_key,
    mnemonic_new,
)
from pytoniq_core.crypto.signature import sign_message

from ..base import BaseContract
from ..codes import CONTRACT_CODES
from ...exceptions import (
    ContractError,
)
from ...protocols import (
    ClientProtocol,
    WalletProtocol,
)
from ...types import (
    AddressLike,
    BaseWalletConfig,
    BaseWalletData,
    BaseWalletParams,
    PrivateKey,
    PublicKey,
    SendMode,
    TransferJettonMessage,
    TransferMessage,
    TransferNFTMessage,
    WorkchainID,
    ContractStateInfo,
)
from ...utils import (
    VALID_MNEMONIC_LENGTHS,
    build_external_msg_any,
    normalize_hash,
    validate_mnemonic,
    to_cell,
)

D = t.TypeVar("D", bound=BaseWalletData)
C = t.TypeVar("C", bound=BaseWalletConfig)
P = t.TypeVar("P", bound=BaseWalletParams)

TWallet = t.TypeVar("TWallet", bound="BaseWallet[t.Any, t.Any, t.Any]")


class BaseWallet(BaseContract, WalletProtocol[D, C, P], abc.ABC):
    _data_model: t.Type[D]
    _config_model: t.Type[C]
    _params_model: t.Type[P]

    MAX_MESSAGES: t.ClassVar[int]

    def __init__(
        self,
        client: ClientProtocol,
        address: Address,
        state_init: t.Optional[StateInit] = None,
        state_info: t.Optional[ContractStateInfo] = None,
        config: t.Optional[C] = None,
        private_key: t.Optional[PrivateKey] = None,
    ) -> None:
        self._config = config
        self._private_key: t.Optional[PrivateKey] = None
        self._public_key: t.Optional[PublicKey] = None

        if private_key is not None:
            self._private_key = private_key
            self._public_key = private_key.public_key
        super().__init__(client, address, state_init, state_info)

    @property
    def state_data(self) -> D:
        return super().state_data

    @property
    def config(self) -> C:
        return t.cast(C, self._config)

    @property
    def public_key(self) -> t.Optional[PublicKey]:
        return self._public_key if self._public_key else None

    @property
    def private_key(self) -> t.Optional[PrivateKey]:
        return self._private_key if self._private_key else None

    @abc.abstractmethod
    async def _build_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[P] = None,
    ) -> Cell: ...

    async def _build_sign_msg_cell(
        self,
        signing_msg: Cell,
        signature: bytes,
    ) -> Cell:
        cell = begin_cell()
        cell.store_bytes(signature)
        cell.store_cell(signing_msg)
        return cell.end_cell()

    async def _build_signed_msg_cell(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[P] = None,
    ) -> Cell:
        if self._private_key is None:
            raise ContractError(
                self,
                f"Cannot sign message: "
                f"`private_key` is not set for wallet `{self.VERSION.value}`.",
            )
        signed_msg = await self._build_msg_cell(messages, params)
        signature = sign_message(signed_msg.hash, self._private_key.keypair.bytes)
        return await self._build_sign_msg_cell(signed_msg, signature)

    @classmethod
    def from_private_key(
        cls: t.Type[TWallet],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[C] = None,
    ) -> TWallet:
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
        cls: t.Type[TWallet],
        client: ClientProtocol,
        mnemonic: t.Union[t.List[str], str],
        validate: bool = True,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[C] = None,
    ) -> t.Tuple[TWallet, PublicKey, PrivateKey, t.List[str]]:
        if isinstance(mnemonic, str):
            mnemonic = mnemonic.strip().lower().split()
        if validate:
            validate_mnemonic(mnemonic)

        pub_key_bytes, priv_key_bytes = mnemonic_to_private_key(mnemonic)
        private_key = PrivateKey(priv_key_bytes)
        public_key = PublicKey(pub_key_bytes)

        wallet = cls.from_private_key(client, private_key, workchain, config)
        return wallet, public_key, private_key, mnemonic

    @classmethod
    def create(
        cls: t.Type[TWallet],
        client: ClientProtocol,
        mnemonic_length: int = 24,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: t.Optional[C] = None,
    ) -> t.Tuple[TWallet, PublicKey, PrivateKey, t.List[str]]:
        cls._validate_mnemonic_length(mnemonic_length)
        mnemonic = mnemonic_new(mnemonic_length)
        return cls.from_mnemonic(client, mnemonic, True, workchain, config)

    async def raw_transfer(
        self,
        messages: t.List[WalletMessage],
        params: t.Optional[P] = None,
    ) -> str:
        await self.refresh()
        self._validate_message_count(messages)
        self._validate_params_type(params)

        body = await self._build_signed_msg_cell(messages, params)
        state_init = self.state_init if not self.is_active else None

        msg = build_external_msg_any(
            dest=self.address,
            body=body,
            state_init=state_init,
        )
        msg_boc = msg.serialize().to_boc().hex()
        normalized_hash = normalize_hash(msg)

        await self.client.send_boc(msg_boc)
        return normalized_hash

    async def transfer(
        self,
        destination: AddressLike,
        value: int,
        body: t.Optional[t.Union[Cell, str]] = None,
        state_init: t.Optional[StateInit] = None,
        send_mode: t.Optional[t.Union[SendMode, int]] = None,
        bounce: t.Optional[bool] = None,
        params: t.Optional[P] = None,
    ) -> str:
        message = TransferMessage(
            destination=destination,
            value=value,
            body=body,
            state_init=state_init,
            send_mode=send_mode,
            bounce=bounce,
        )
        return await self.transfer_message(message, params)

    async def transfer_message(
        self,
        message: t.Union[
            TransferMessage,
            TransferNFTMessage,
            TransferJettonMessage,
        ],
        params: t.Optional[P] = None,
    ) -> str:
        message = await message.to_wallet_msg(self)
        return await self.raw_transfer([message], params)

    async def batch_transfer_message(
        self,
        messages: t.List[
            t.Union[
                TransferMessage,
                TransferNFTMessage,
                TransferJettonMessage,
            ]
        ],
        params: t.Optional[P] = None,
    ) -> str:
        messages = [await m.to_wallet_msg(self) for m in messages]
        return await self.raw_transfer(messages, params)

    @classmethod
    def _validate_config_type(
        cls: t.Type[TWallet],
        config: C,
    ) -> None:
        if not isinstance(config, cls._config_model):
            raise ContractError(
                cls,
                f"Invalid contract config type for `{cls.VERSION.value}`. "
                f"Expected {cls._config_model.__name__}, "
                f"got {type(config).__name__}.",
            )

    @classmethod
    def _validate_params_type(
        cls: t.Type[TWallet],
        params: t.Optional[P] = None,
    ) -> None:
        if params is not None and not isinstance(params, cls._params_model):
            raise ContractError(
                cls,
                f"Invalid params type for `{cls.VERSION.value}`. "
                f"Expected {cls._params_model.__name__}, "
                f"got {type(params).__name__ if params is not None else 'None'}.",
            )

    @classmethod
    def _validate_message_count(
        cls: t.Type[TWallet],
        messages: t.List[WalletMessage],
    ) -> None:
        if len(messages) > cls.MAX_MESSAGES:
            raise ContractError(
                cls.__name__,
                f"For `{cls.VERSION.value}`, "
                f"maximum messages amount is {cls.MAX_MESSAGES}, "
                f"but got {len(messages)}.",
            )

    @classmethod
    def _validate_mnemonic_length(
        cls: t.Type[TWallet],
        mnemonic_length: int,
    ) -> None:
        if mnemonic_length not in VALID_MNEMONIC_LENGTHS:
            raise ContractError(
                cls,
                f"Invalid mnemonic length: {mnemonic_length}. "
                f"Expected one of {VALID_MNEMONIC_LENGTHS}.",
            )
