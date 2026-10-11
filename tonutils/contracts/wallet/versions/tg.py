from __future__ import annotations

import typing as t

from ton_core import (
    WALLET_TG_KEY_CHANGE_SALT,
    WALLET_TG_KEY_ROTATION_PROOF_TAG,
    WALLET_TG_SUBWALLET_ID,
    WALLET_TG_SUBWALLET_ID_TESTNET,
    Cell,
    ContractVersion,
    MnemonicType,
    NetworkGlobalID,
    OpCode,
    PrivateKey,
    PublicKey,
    SendMode,
    SignatureDomain,
    WalletMessage,
    WalletTgChangePublicKeyBody,
    WalletTgConfig,
    WalletTgData,
    WalletTgKeyChangedBody,
    WalletTgParams,
    WorkchainID,
    begin_cell,
    calc_valid_until,
    multichain_mnemonic_is_valid,
    multichain_mnemonic_to_private_key,
    sign_message,
    ton_mnemonic_is_valid,
    words,
)

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.wallet.base import BaseWallet
from tonutils.contracts.wallet.messages import ExternalMessage
from tonutils.contracts.wallet.methods import (
    GetPublicKeyGetMethod,
    GetSubwalletIDGetMethod,
    RevisionGetMethod,
    SeqnoGetMethod,
)
from tonutils.exceptions import ContractError

_TWalletTg = t.TypeVar("_TWalletTg", bound="WalletTg")


class WalletTg(
    BaseWallet[
        WalletTgData,
        WalletTgConfig,
        WalletTgParams,
    ],
    SeqnoGetMethod,
    GetPublicKeyGetMethod,
    GetSubwalletIDGetMethod,
    RevisionGetMethod,
):
    """Telegram wallet (WalletTg) -- bytecode in config, key rotation, up to 255 messages."""

    _data_model = WalletTgData
    _config_model = WalletTgConfig
    _params_model = WalletTgParams
    _mnemonic_type = MnemonicType.MULTICHAIN
    VERSION = ContractVersion.WalletTg
    MAX_MESSAGES = 255

    @classmethod
    def from_private_key(
        cls: type[_TWalletTg],
        client: ClientProtocol,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: WalletTgConfig | None = None,
    ) -> _TWalletTg:
        """Create wallet from a private key.

        :param client: TON client.
        :param private_key: Ed25519 private key.
        :param workchain: Target workchain.
        :param config: Wallet configuration, or ``None``.
        :return: New wallet instance.
        """
        config = config or cls._config_model()
        cls._validate_config_type(config)

        if config.subwallet_id is None:
            config.subwallet_id = (
                WALLET_TG_SUBWALLET_ID_TESTNET if client.network == NetworkGlobalID.TESTNET else WALLET_TG_SUBWALLET_ID
            )

        return super().from_private_key(client, private_key, workchain, config)

    @classmethod
    def from_mnemonic(
        cls: type[_TWalletTg],
        client: ClientProtocol,
        mnemonic: list[str] | str,
        validate: bool = True,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: WalletTgConfig | None = None,
        mnemonic_type: MnemonicType | None = None,
    ) -> tuple[_TWalletTg, PublicKey, PrivateKey, list[str]]:
        """Create wallet from a Telegram wallet mnemonic.

        A 24-word mnemonic holds two 12-word Multichain (BIP-39) halves: the
        anchor half (words 1-12) derives the address and never changes, the
        signing half (words 13-24) holds the current key and is replaced on
        each rotation. A 12-word mnemonic is the anchor half of a wallet whose
        key was never rotated.

        :param client: TON client.
        :param mnemonic: Mnemonic of 12 or 24 words (list or space-separated string).
        :param validate: Validate words and the checksum of each half.
        :param workchain: Target workchain.
        :param config: Wallet configuration, or ``None``.
        :param mnemonic_type: ``MnemonicType.MULTICHAIN`` or ``None``.
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list) with the signing key pair.
        """
        if validate:
            cls.validate_mnemonic(mnemonic, mnemonic_type)
        halves = cls._mnemonic_halves(mnemonic, mnemonic_type)
        anchor_key = PrivateKey(multichain_mnemonic_to_private_key(halves[0])[1])
        signing_key = PrivateKey(multichain_mnemonic_to_private_key(halves[-1])[1])

        anchored = cls.from_private_key(client, anchor_key, workchain, config)
        wallet = cls(client, anchored.address, anchored.state_init, None, anchored.config, signing_key)
        return wallet, signing_key.public_key, signing_key, [w for half in halves for w in half]

    @classmethod
    def create(
        cls: type[_TWalletTg],
        client: ClientProtocol,
        mnemonic_length: int | None = None,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: WalletTgConfig | None = None,
        mnemonic_type: MnemonicType | None = None,
    ) -> tuple[_TWalletTg, PublicKey, PrivateKey, list[str]]:
        """Create a new wallet with a random 12-word Multichain (BIP-39) mnemonic.

        :param client: TON client.
        :param mnemonic_length: ``12`` or ``None``.
        :param workchain: Target workchain.
        :param config: Wallet configuration, or ``None``.
        :param mnemonic_type: ``MnemonicType.MULTICHAIN`` or ``None``.
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list).
        :raises ContractError: If another length or scheme is requested.
        """
        if mnemonic_length not in (None, 12) or mnemonic_type not in (None, MnemonicType.MULTICHAIN):
            raise ContractError(
                cls,
                f"For `{cls.VERSION!r}`, `create()` generates only 12-word Multichain (BIP-39) mnemonics.",
            )
        return super().create(client, mnemonic_length, workchain, config, mnemonic_type)

    async def rotate_mnemonic(
        self,
        new_mnemonic: list[str] | str,
        params: WalletTgParams | None = None,
    ) -> ExternalMessage:
        """Build, sign, and send a key-rotation request to a new mnemonic.

        ``new_mnemonic`` is 24 words: words 1-12 of the current mnemonic, which
        keep the address, and a new 12-word half that becomes the signing key
        (generate it with ``multichain_mnemonic_new()``).
        Store it before the call: it is the only copy of the new key. After the
        request is accepted on-chain, open the wallet with ``from_mnemonic()``.

        :param new_mnemonic: New 24-word mnemonic (list or space-separated string).
        :param params: Transaction parameters, or ``None``.
        :return: Sent ``ExternalMessage``.
        :raises ValueError: If the mnemonic is invalid or not 24 words.
        :raises ContractError: If words 1-12 do not derive this wallet, or words 13-24
            repeat words 1-12 or the current key.
        """
        initial = self._config or WalletTgConfig(subwallet_id=self._resolve_subwallet_id())
        rotated, _, private_key, mnemonic = self.from_mnemonic(
            self.client,
            new_mnemonic,
            workchain=WorkchainID(self.address.wc),
            config=WalletTgConfig(**initial.to_dict()),
        )
        if len(mnemonic) != 24:
            raise ValueError(f"Invalid new mnemonic length: {len(mnemonic)}. Expected 24.")
        if rotated.address != self.address:
            raise ContractError(
                self,
                f"Words 1-12 of the new mnemonic do not derive wallet at {self.address.to_str()}.",
                hint="Keep words 1-12 of the current mnemonic.",
            )
        if mnemonic[:12] == mnemonic[12:]:
            raise ContractError(
                self,
                f"For `{self.VERSION!r}`, words 13-24 of the new mnemonic must differ from words 1-12.",
            )

        external_msg = await self._build_rotation_message(private_key, params)
        await self.client.send_message(external_msg.as_hex)
        return external_msg

    async def _build_signed_msg_cell(
        self,
        messages: list[WalletMessage],
        params: WalletTgParams | None = None,
    ) -> Cell:
        """Build and sign a message cell, checking the signing key first.

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or ``None``.
        :return: Signed message cell.
        """
        self._check_signing_key()
        return await super()._build_signed_msg_cell(messages, params)

    async def _build_rotation_message(
        self,
        new_private_key: PrivateKey,
        params: WalletTgParams | None = None,
    ) -> ExternalMessage:
        """Build a signed key-rotation external message.

        The request is signed twice: the message itself by the current key,
        and a key-rotation proof payload (tag + wallet address) by the new
        key, proving ownership of the key being installed. The contract checks
        both signatures the same way, so both use the network signature domain.
        The request also carries the old private key encrypted with the new one.

        :param new_private_key: Ed25519 private key to rotate to.
        :param params: Transaction parameters, or ``None``.
        :return: Signed ``ExternalMessage``.
        :raises ContractError: If private key is not set, or the new key equals the current one.
        """
        if self._private_key is None:
            raise ContractError(
                self,
                f"Cannot sign message: `private_key` is not set for wallet `{self.VERSION!r}`.",
                hint="Use .from_mnemonic() or .from_private_key() to create a wallet with signing capability.",
            )
        if new_private_key.public_key.as_bytes == self._private_key.public_key.as_bytes:
            raise ContractError(
                self,
                f"For `{self.VERSION!r}`, the new public key must differ from the current one.",
            )

        await self.refresh()
        self._check_signing_key()
        params = params or self._params_model()
        self._validate_params_type(params)
        op_code = params.op_code if params.op_code is not None else OpCode.WALLET_TG_CHANGE_PUBLIC_KEY_EXTERNAL

        domain = SignatureDomain(self.client.network)
        proof_payload = begin_cell()
        proof_payload.store_uint(WALLET_TG_KEY_ROTATION_PROOF_TAG, 96)
        proof_payload.store_int(self.address.wc, 8)
        proof_payload.store_bytes(self.address.hash_part)
        rotation_signature = sign_message(
            domain.data_to_sign(proof_payload.end_cell().hash),
            new_private_key.keypair.as_bytes,
        )

        key_changed = WalletTgKeyChangedBody.from_keys(self._private_key, new_private_key, WALLET_TG_KEY_CHANGE_SALT)
        seqno, valid_until = self._resolve_seqno_and_valid_until(params)
        signing_msg = WalletTgChangePublicKeyBody(
            new_public_key=new_private_key.public_key,
            rotation_signature=rotation_signature,
            encrypted_old_private_key=key_changed.encrypted_old_private_key,
            seqno=seqno,
            valid_until=valid_until,
            subwallet_id=self._resolve_subwallet_id(),
            op_code=op_code,
        ).serialize()

        signature = sign_message(
            domain.data_to_sign(signing_msg.hash),
            self._private_key.keypair.as_bytes,
        )
        body = await self._build_sign_msg_cell(signing_msg, signature)
        state_init = self.state_init if not self.is_active else None
        return ExternalMessage(dest=self.address, body=body, state_init=state_init)

    async def _build_msg_cell(
        self,
        messages: list[WalletMessage],
        params: WalletTgParams | None = None,
    ) -> Cell:
        """Build unsigned request cell (signed-request body).

        :param messages: Internal messages to include.
        :param params: Transaction parameters, or ``None``.
        :return: Unsigned request cell.
        """
        params = params or self._params_model()

        if not messages:
            raise ContractError(
                self,
                f"For `{self.VERSION!r}`, at least one message is required.",
            )

        op_code = params.op_code
        if op_code is None:
            op_code = (
                OpCode.WALLET_TG_SEND_ONE_MESSAGE_EXTERNAL
                if len(messages) == 1
                else OpCode.WALLET_TG_SEND_BULK_MESSAGES_EXTERNAL
            )
        one_message = op_code in (
            OpCode.WALLET_TG_SEND_ONE_MESSAGE_INTERNAL,
            OpCode.WALLET_TG_SEND_ONE_MESSAGE_EXTERNAL,
        )
        if one_message and len(messages) != 1:
            raise ContractError(
                self,
                f"For `{self.VERSION!r}`, opcode {op_code!r} carries exactly one message, got {len(messages)}.",
            )
        self._validate_send_modes(messages, op_code)

        cell = begin_cell()
        cell.store_cell(self._build_request_header(op_code, params))
        if one_message:
            cell.store_cell(messages[0].serialize())
        else:
            cell.store_uint(len(messages), 8)
            cell.store_maybe_ref(self._build_msg_array(messages))
        return cell.end_cell()

    def _build_request_header(
        self,
        op_code: int,
        params: WalletTgParams,
    ) -> Cell:
        """Build the common request prefix: opcode plus the seqno header.

        :param op_code: Request opcode.
        :param params: Transaction parameters.
        :return: Header ``Cell`` (opcode, subwallet ID, valid-until, seqno).
        """
        seqno, valid_until = self._resolve_seqno_and_valid_until(params)

        cell = begin_cell()
        cell.store_uint(op_code, 32)
        cell.store_uint(self._resolve_subwallet_id(), 32)
        cell.store_uint(valid_until, 32)
        cell.store_uint(seqno, 32)
        return cell.end_cell()

    def _resolve_seqno_and_valid_until(self, params: WalletTgParams) -> tuple[int, int]:
        """Resolve request seqno and expiration from params or on-chain state.

        :param params: Transaction parameters.
        :return: Tuple of (seqno, valid_until).
        """
        seqno = params.seqno if params.seqno is not None else self.state_data.seqno if self.is_active else 0
        valid_until = params.valid_until if params.valid_until is not None else calc_valid_until(seqno)
        return seqno, valid_until

    @classmethod
    def _build_msg_array(cls, messages: list[WalletMessage]) -> Cell:
        """Encode messages as the WalletTg array chunk chain.

        Intermediate chunks hold 3 items (the first ref is ``next``),
        the last chunk holds up to 4 items and has no ``next`` ref.

        :param messages: Wallet messages to encode.
        :return: Head chunk ``Cell`` of the chain.
        """
        chunks: list[list[WalletMessage]] = []
        rest = messages
        while len(rest) > 4:
            chunks.append(rest[:3])
            rest = rest[3:]
        chunks.append(rest)

        head: Cell | None = None
        for chunk in reversed(chunks):
            cell = begin_cell()
            cell.store_maybe_ref(head)
            for msg in chunk:
                cell.store_cell(msg.serialize())
            head = cell.end_cell()

        assert head is not None
        return head

    @classmethod
    def _validate_send_modes(
        cls,
        messages: list[WalletMessage],
        op_code: int,
    ) -> None:
        """Validate send modes for the external path.

        The contract rejects external requests whose messages lack
        ``SEND_MODE_IGNORE_ERRORS``; failing locally avoids burning a seqno.

        :param messages: Messages to validate.
        :param op_code: Request opcode.
        :raises ContractError: If an external message lacks the +2 flag.
        """
        if op_code not in (
            OpCode.WALLET_TG_SEND_ONE_MESSAGE_EXTERNAL,
            OpCode.WALLET_TG_SEND_BULK_MESSAGES_EXTERNAL,
        ):
            return
        for i, msg in enumerate(messages):
            if not msg.send_mode & SendMode.IGNORE_ERRORS:
                raise ContractError(
                    cls,
                    f"For `{cls.VERSION!r}`, external messages require "
                    f"SEND_MODE_IGNORE_ERRORS (+2), but message #{i} has send_mode={msg.send_mode}.",
                    hint="Add SendMode.IGNORE_ERRORS to the message send mode.",
                )

    def _resolve_subwallet_id(self) -> int:
        """Return subwallet ID from config, or from on-chain state.

        A wallet opened by address has no config: the subwallet ID is then
        read from the refreshed on-chain storage.
        """
        if self._config is not None and self._config.subwallet_id is not None:
            return self._config.subwallet_id
        return self.state_data.subwallet_id

    def _check_signing_key(self) -> None:
        """Check that the signing key controls the wallet, on refreshed state.

        An active wallet accepts only its current on-chain key; an undeployed
        one is deployed with the anchor key, so a rotated key cannot deploy it.

        :raises ContractError: If the signing key does not control the wallet.
        """
        if self._public_key is None:
            return
        if self.is_active:
            onchain_key = self.state_data.public_key
            if onchain_key.as_bytes != self._public_key.as_bytes:
                raise ContractError(
                    self,
                    f"Signing key does not control wallet at {self.address.to_str()}: "
                    f"on-chain public key is {onchain_key.as_hex}, this key is {self._public_key.as_hex}.",
                    hint="The wallet key was rotated; use the current mnemonic.",
                )
        elif self._config is not None and self._config.public_key is not None:
            if self._config.public_key.as_bytes != self._public_key.as_bytes:
                raise ContractError(
                    self,
                    f"Wallet at {self.address.to_str()} is not deployed; only words 1-12 can deploy it.",
                    hint="Open the wallet with words 1-12 to deploy it.",
                )

    @classmethod
    def _mnemonic_halves(
        cls,
        mnemonic: list[str] | str,
        mnemonic_type: MnemonicType | None,
    ) -> list[list[str]]:
        """Normalize a Telegram wallet mnemonic and split it into 12-word halves.

        :param mnemonic: Mnemonic (list or space-separated string).
        :param mnemonic_type: ``MnemonicType.MULTICHAIN`` or ``None``.
        :return: ``[anchor]`` for 12 words, ``[anchor, signing]`` for 24.
        :raises ValueError: If the scheme is not Multichain, or the length is not 12 or 24.
        """
        if mnemonic_type not in (None, MnemonicType.MULTICHAIN):
            raise ValueError(f"{cls.__name__} supports only Multichain (BIP-39) mnemonics.")
        if isinstance(mnemonic, str):
            mnemonic = mnemonic.strip().lower().split()
        else:
            mnemonic = [w.strip().lower() for w in mnemonic]
        if len(mnemonic) not in (12, 24):
            raise ValueError(f"Invalid mnemonic length: {len(mnemonic)}. Expected 12 or 24.")
        return [mnemonic[:12], mnemonic[12:]] if len(mnemonic) == 24 else [mnemonic]

    @classmethod
    def validate_mnemonic(
        cls,
        mnemonic: str | list[str],
        mnemonic_type: MnemonicType | None = None,
    ) -> None:
        """Validate a Telegram wallet mnemonic.

        :param mnemonic: Mnemonic of 12 or 24 words (list or space-separated string).
        :param mnemonic_type: ``MnemonicType.MULTICHAIN`` or ``None``.
        :raises ValueError: If length is invalid, words are not in the wordlist, or a half's checksum fails.
        """
        halves = cls._mnemonic_halves(mnemonic, mnemonic_type)
        mnemonic_words = [w for half in halves for w in half]
        invalid = [(i + 1, w) for i, w in enumerate(mnemonic_words) if w not in words]
        if invalid:
            formatted = ", ".join(f"{idx}. {word}" for idx, word in invalid)
            raise ValueError(f"Invalid mnemonic word(s): {formatted}")
        invalid_halves = [i for i, half in enumerate(halves) if not multichain_mnemonic_is_valid(half)]
        if not invalid_halves:
            return
        if ton_mnemonic_is_valid(mnemonic_words):
            raise ValueError(f"TON mnemonics are not supported by {cls.__name__}; use `from_private_key()`.")
        first = invalid_halves[0] * 12
        raise ValueError(
            f"Invalid mnemonic checksum: words {first + 1}-{first + 12} are not a valid Multichain (BIP-39) mnemonic."
        )
