from __future__ import annotations

import typing as t

from ton_core import (
    WALLET_TG_KEY_CHANGE_SALT,
    WALLET_TG_KEY_ROTATION_PROOF_TAG,
    WALLET_TG_SUBWALLET_ID,
    WALLET_TG_SUBWALLET_ID_TESTNET,
    Address,
    AddressLike,
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
    sign_message,
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
    async def from_address_and_private_key(
        cls: type[_TWalletTg],
        client: ClientProtocol,
        address: AddressLike,
        private_key: PrivateKey,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: WalletTgConfig | None = None,
    ) -> _TWalletTg:
        """Open an existing wallet by address with its current signing key.

        After an on-chain key rotation the wallet keeps its original address
        while the signing key is new, so ``from_private_key`` would derive a
        different (empty) address. This constructor binds the key to a known
        address instead, verifying that the key actually controls it: against
        on-chain storage for an active wallet, against the derived address
        for an undeployed one.

        :param client: TON client.
        :param address: Wallet address.
        :param private_key: Ed25519 private key.
        :param workchain: Target workchain, used to derive the address of an undeployed wallet.
        :param config: Wallet configuration, or ``None``.
        :return: Wallet instance bound to the address with signing capability.
        :raises ContractError: If the key does not control the address.
        """
        if isinstance(address, str):
            address = Address(address)

        info = await cls._load_info(client, address)
        wallet = cls(client, address, None, info, None, private_key)
        if wallet.is_active:
            onchain_key = wallet.state_data.public_key
            if onchain_key.as_bytes != private_key.public_key.as_bytes:
                raise ContractError(
                    cls,
                    f"Private key does not control wallet at {address.to_str()}: "
                    f"on-chain public key is {onchain_key.as_hex}, this key derives {private_key.public_key.as_hex}.",
                    hint="The wallet key may have been rotated; use the current key.",
                )
            return wallet

        derived = cls.from_private_key(client, private_key, workchain, config)
        if derived.address != address:
            raise ContractError(
                cls,
                f"Address {address.to_str()} is not deployed and does not derive from this key "
                f"(derived address: {derived.address.to_str()}).",
                hint="Check the key and network, or pass the wallet's workchain and config.",
            )
        return cls(client, address, derived.state_init, info, derived.config, private_key)

    @classmethod
    async def from_address_and_mnemonic(
        cls: type[_TWalletTg],
        client: ClientProtocol,
        address: AddressLike,
        mnemonic: list[str] | str,
        validate: bool = True,
        workchain: WorkchainID = WorkchainID.BASECHAIN,
        config: WalletTgConfig | None = None,
        mnemonic_type: MnemonicType | None = None,
    ) -> tuple[_TWalletTg, PublicKey, PrivateKey, list[str]]:
        """Open an existing wallet by address with its current mnemonic.

        Mnemonic counterpart of ``from_address_and_private_key``; use it for
        a wallet whose key was rotated on-chain (the address no longer
        derives from the mnemonic).

        :param client: TON client.
        :param address: Wallet address.
        :param mnemonic: Mnemonic (list or space-separated string).
        :param validate: Validate mnemonic length, words and checksum.
        :param workchain: Target workchain, used to derive the address of an undeployed wallet.
        :param config: Wallet configuration, or ``None``.
        :param mnemonic_type: Key derivation scheme, or ``None`` to detect it by checksum
            (the wallet scheme if not validated).
        :return: Tuple of (wallet, public_key, private_key, mnemonic_list).
        :raises ContractError: If the key does not control the address.
        """
        public_key, private_key, mnemonic = cls._mnemonic_to_keys(mnemonic, validate, mnemonic_type)
        wallet = await cls.from_address_and_private_key(client, address, private_key, workchain, config)
        return wallet, public_key, private_key, mnemonic

    async def build_change_public_key_message(
        self,
        new_private_key: PrivateKey,
        params: WalletTgParams | None = None,
        salt: bytes = WALLET_TG_KEY_CHANGE_SALT,
    ) -> ExternalMessage:
        """Build a signed key-rotation external message.

        The request is signed twice: the message itself by the current key,
        and a key-rotation proof payload (tag + wallet address) by the new
        key, proving ownership of the key being installed. The proof is signed
        over the raw payload hash, without a network signature-domain prefix.
        The request also carries the old private key encrypted with the new one.

        :param new_private_key: Ed25519 private key to rotate to.
        :param params: Transaction parameters, or ``None``.
        :param salt: Key-change salt; with a custom one, clients using the default salt cannot recover the old key.
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
        params = params or self._params_model()
        self._validate_params_type(params)
        op_code = params.op_code if params.op_code is not None else OpCode.WALLET_TG_CHANGE_PUBLIC_KEY_EXTERNAL

        proof_payload = begin_cell()
        proof_payload.store_uint(WALLET_TG_KEY_ROTATION_PROOF_TAG, 96)
        proof_payload.store_int(self.address.wc, 8)
        proof_payload.store_bytes(self.address.hash_part)
        rotation_signature = sign_message(
            proof_payload.end_cell().hash,
            new_private_key.keypair.as_bytes,
        )

        key_changed = WalletTgKeyChangedBody.from_keys(self._private_key, new_private_key, salt)
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

        domain = SignatureDomain(self.client.network)
        signature = sign_message(
            domain.data_to_sign(signing_msg.hash),
            self._private_key.keypair.as_bytes,
        )
        body = await self._build_sign_msg_cell(signing_msg, signature)
        state_init = self.state_init if not self.is_active else None
        return ExternalMessage(dest=self.address, body=body, state_init=state_init)

    async def change_public_key(
        self,
        new_private_key: PrivateKey,
        params: WalletTgParams | None = None,
        salt: bytes = WALLET_TG_KEY_CHANGE_SALT,
    ) -> ExternalMessage:
        """Build, sign, and send a key-rotation request.

        On success the on-chain public key changes; this instance keeps the
        old signing key, so reopen the wallet with
        ``from_address_and_private_key`` for further use.

        :param new_private_key: Ed25519 private key to rotate to.
        :param params: Transaction parameters, or ``None``.
        :param salt: Key-change salt; with a custom one, clients using the default salt cannot recover the old key.
        :return: Sent ``ExternalMessage``.
        """
        external_msg = await self.build_change_public_key_message(new_private_key, params, salt)
        await self.client.send_message(external_msg.as_hex)
        return external_msg

    async def change_public_key_from_mnemonic(
        self,
        new_mnemonic: list[str] | str,
        validate: bool = True,
        params: WalletTgParams | None = None,
        salt: bytes = WALLET_TG_KEY_CHANGE_SALT,
        mnemonic_type: MnemonicType | None = None,
    ) -> tuple[ExternalMessage, PublicKey, PrivateKey, list[str]]:
        """Build, sign, and send a key-rotation request to a new mnemonic.

        Mnemonic counterpart of ``change_public_key``. After the request is
        accepted on-chain, reopen the wallet with
        ``from_address_and_mnemonic(client, wallet.address, new_mnemonic)``.

        :param new_mnemonic: Mnemonic to rotate to (list or space-separated string).
        :param validate: Validate mnemonic length, words and checksum.
        :param params: Transaction parameters, or ``None``.
        :param salt: Key-change salt; with a custom one, clients using the default salt cannot recover the old key.
        :param mnemonic_type: Key derivation scheme of the new mnemonic, or ``None`` to detect it by checksum
            (the wallet scheme if not validated).
        :return: Tuple of (external_message, public_key, private_key, mnemonic_list) for the new key.
        """
        public_key, private_key, mnemonic = self._mnemonic_to_keys(new_mnemonic, validate, mnemonic_type)
        external_msg = await self.change_public_key(private_key, params, salt)
        return external_msg, public_key, private_key, mnemonic

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

        After a key rotation the wallet is controlled via address + new key
        (``from_address_and_private_key``), with no config: the subwallet ID
        is then read from the refreshed on-chain storage.
        """
        if self._config is not None and self._config.subwallet_id is not None:
            return self._config.subwallet_id
        return self.state_data.subwallet_id
