from __future__ import annotations

import abc
import typing as t

from ton_core import (
    DEFAULT_SENDMODE,
    Address,
    AddressLike,
    Cell,
    CurrencyCollection,
    DNSCategory,
    DNSRecordWallet,
    ExternalMsgInfo,
    InternalMsgInfo,
    JettonTransferBody,
    NFTTransferBody,
    PublicKey,
    SendMode,
    StateInit,
    TextCipher,
    TextCommentBody,
    WalletMessage,
    cell_to_b64,
    cell_to_hex,
    normalize_hash,
    to_nano,
)
from ton_core import MessageAny as MessageAnyBase

from tonutils.contracts.jetton.methods import get_wallet_address_get_method
from tonutils.contracts.wallet.methods import get_public_key_get_method
from tonutils.contracts.wallet.protocol import WalletProtocol
from tonutils.exceptions import ContractError, RunGetMethodError


class MessageAny(MessageAnyBase):
    """Extended message with serialization helpers."""

    def to_cell(self) -> Cell:
        """Serialize to ``Cell``."""
        return self.serialize()

    def to_boc(self) -> bytes:
        """Serialize to BoC bytes."""
        return self.to_cell().to_boc()

    @property
    def as_hex(self) -> str:
        """Hex-encoded BoC string."""
        return cell_to_hex(self.to_cell())

    @property
    def as_b64(self) -> str:
        """Base64-encoded BoC string."""
        return cell_to_b64(self.to_cell())


class ExternalMessage(MessageAny):
    """External message for sending transactions to the TON blockchain."""

    def __init__(
        self,
        src: Address | None = None,
        dest: Address | None = None,
        import_fee: int = 0,
        body: Cell | None = None,
        state_init: StateInit | None = None,
    ) -> None:
        """Initialize the external message.

        :param src: Source address, or ``None``.
        :param dest: Destination contract address, or ``None``.
        :param import_fee: Import fee in nanotons.
        :param body: Signed message body cell, or ``None``.
        :param state_init: ``StateInit`` for deployment, or ``None``.
        """
        info = ExternalMsgInfo(src, dest, import_fee)
        super().__init__(info, state_init, body or Cell.empty())

    @property
    def normalized_hash(self) -> str:
        """Normalized message hash as hex string."""
        return normalize_hash(self)


class InternalMessage(MessageAny):
    """Internal message for on-chain contract-to-contract communication."""

    def __init__(
        self,
        ihr_disabled: bool | None = True,
        bounce: bool | None = None,
        bounced: bool | None = False,
        src: AddressLike | None = None,
        dest: AddressLike | None = None,
        value: CurrencyCollection | int = 0,
        ihr_fee: int = 0,
        fwd_fee: int = 0,
        created_lt: int = 0,
        created_at: int = 0,
        body: Cell | None = None,
        state_init: StateInit | None = None,
    ) -> None:
        """Initialize the internal message.

        :param ihr_disabled: Disable instant hypercube routing.
        :param bounce: Bounce on error, or ``None`` for auto-detect.
        :param bounced: Whether this is a bounced message.
        :param src: Source address, or ``None``.
        :param dest: Destination address, or ``None``.
        :param value: Amount in nanotons or ``CurrencyCollection``.
        :param ihr_fee: IHR fee in nanotons.
        :param fwd_fee: Forward fee in nanotons.
        :param created_lt: Logical time when created.
        :param created_at: Unix timestamp when created.
        :param body: Message body cell, or ``None``.
        :param state_init: ``StateInit`` for deployment, or ``None``.
        """
        if isinstance(src, str):
            src = Address(src)
        if isinstance(dest, str):
            dest = Address(dest)
        if bounce is None:
            bounce = dest.is_bounceable if dest and isinstance(dest, Address) else False
        if body is None:
            body = Cell.empty()
        if isinstance(value, int):
            value = CurrencyCollection(value)

        info = InternalMsgInfo(
            ihr_disabled=ihr_disabled,
            bounce=bounce,
            bounced=bounced,
            src=src,
            dest=dest,
            value=value,
            ihr_fee=ihr_fee,
            fwd_fee=fwd_fee,
            created_lt=created_lt,
            created_at=created_at,
        )
        super().__init__(info, state_init, body)


class BaseMessageBuilder(abc.ABC):
    """Abstract base for constructing ``WalletMessage`` instances."""

    @abc.abstractmethod
    async def build(self, wallet: WalletProtocol[t.Any, t.Any, t.Any]) -> WalletMessage:
        """Build a ``WalletMessage`` for the given wallet.

        :param wallet: Source wallet instance.
        :return: Constructed ``WalletMessage``.
        """


async def _resolve_destination(wallet: WalletProtocol[t.Any, t.Any, t.Any], destination: AddressLike) -> Address:
    """Resolve a recipient address.

    A ``.ton`` or ``.t.me`` domain resolves to its wallet record, returned non-bounceable.

    :param wallet: Sender wallet.
    :param destination: Recipient address or domain.
    :return: Recipient address.
    :raises ContractError: If the domain is not registered or has no wallet record.
    """
    if isinstance(destination, Address):
        return destination
    if "." not in destination:
        return Address(destination)

    record = await wallet.client.dnsresolve(destination, DNSCategory.WALLET)
    if not isinstance(record, DNSRecordWallet):
        raise ContractError(wallet, f"Domain `{destination}` is not registered or has no wallet record.")
    address = Address(record.value)
    address.is_bounceable = False
    return address


async def _build_payload(
    wallet: WalletProtocol[t.Any, t.Any, t.Any],
    payload: Cell | str | None,
    recipient: Address,
    encrypt: bool,
    recipient_public_key: PublicKey | None,
) -> Cell | None:
    """Build a message payload.

    A text becomes a comment, encrypted for the recipient with ``encrypt``.

    :param wallet: Sender wallet; its address is the encryption salt.
    :param payload: Payload (``Cell`` or text comment), or ``None``.
    :param recipient: Recipient wallet address.
    :param encrypt: Encrypt the text comment.
    :param recipient_public_key: Recipient public key, or ``None`` to fetch it.
    :return: Payload cell, or ``None``.
    :raises ValueError: If ``encrypt`` is set without a text comment.
    :raises ContractError: If the recipient public key cannot be fetched,
        or ``encrypt`` is set on a wallet without a private key.
    """
    if not isinstance(payload, str):
        if encrypt:
            raise ValueError("`encrypt` requires a text comment.")
        return payload
    if not encrypt:
        return TextCommentBody(payload).serialize()
    if wallet.private_key is None:
        raise ContractError(
            wallet,
            f"Cannot encrypt comment: `private_key` is not set for wallet `{wallet.VERSION!r}`.",
            hint="Use .from_mnemonic() or .from_private_key() to create a wallet with signing capability.",
        )
    public_key = recipient_public_key
    if public_key is None:
        try:
            public_key = await get_public_key_get_method(wallet.client, recipient)
        except RunGetMethodError as exc:
            raise ContractError(
                wallet,
                f"Cannot get public key of `{recipient.to_str()}`.",
                hint="The recipient wallet may be undeployed; pass `recipient_public_key`.",
            ) from exc
    return TextCipher.encrypt(payload, wallet.address, wallet.private_key, public_key)


class TONTransferBuilder(BaseMessageBuilder):
    """Builder for simple TON transfer messages."""

    def __init__(
        self,
        destination: AddressLike,
        amount: int,
        body: Cell | str | None = None,
        state_init: StateInit | None = None,
        send_mode: SendMode | int = DEFAULT_SENDMODE,
        bounce: bool | None = None,
        encrypt: bool = False,
        recipient_public_key: PublicKey | None = None,
    ) -> None:
        """Initialize the TON transfer builder.

        :param destination: Recipient address or ``.ton``/``.t.me`` domain.
        :param amount: Amount in nanotons.
        :param body: Body (``Cell`` or text comment), or ``None``.
        :param state_init: ``StateInit`` for deployment, or ``None``.
        :param send_mode: Send mode flags.
        :param bounce: Bounce on error, or ``None`` for auto-detect.
        :param encrypt: Encrypt the text comment for the recipient.
        :param recipient_public_key: Recipient public key for ``encrypt``, or ``None`` to fetch it.
        """
        self.destination = destination
        self.amount = amount
        self.body = body
        self.state_init = state_init
        self.send_mode = send_mode
        self.bounce = bounce
        self.encrypt = encrypt
        self.recipient_public_key = recipient_public_key

    async def build(self, wallet: WalletProtocol[t.Any, t.Any, t.Any]) -> WalletMessage:
        """Build a TON transfer ``WalletMessage``.

        :param wallet: Source wallet instance.
        :return: Constructed ``WalletMessage``.
        :raises ValueError: If ``encrypt`` is set without a text comment.
        :raises ContractError: If the destination or recipient public key cannot be resolved,
            or ``encrypt`` is set on a wallet without a private key.
        """
        destination = await _resolve_destination(wallet, self.destination)
        body = await _build_payload(wallet, self.body, destination, self.encrypt, self.recipient_public_key)
        return WalletMessage(
            send_mode=self.send_mode,
            message=InternalMessage(
                dest=destination,
                value=self.amount,
                body=body,
                state_init=self.state_init,
                bounce=self.bounce,
            ),
        )


class NFTTransferBuilder(BaseMessageBuilder):
    """Builder for NFT transfer messages."""

    def __init__(
        self,
        destination: AddressLike,
        nft_address: AddressLike,
        response_address: AddressLike | None = None,
        custom_payload: Cell | None = None,
        forward_payload: Cell | str | None = None,
        forward_amount: int = 1,
        amount: int = to_nano("0.05"),
        query_id: int = 0,
        send_mode: SendMode | int = DEFAULT_SENDMODE,
        bounce: bool | None = None,
        encrypt: bool = False,
        recipient_public_key: PublicKey | None = None,
    ) -> None:
        """Initialize the NFT transfer builder.

        :param destination: New NFT owner address or ``.ton``/``.t.me`` domain.
        :param nft_address: NFT item contract address.
        :param response_address: Address for excess funds, or ``None`` for wallet address.
        :param custom_payload: Custom payload cell, or ``None``.
        :param forward_payload: Payload to forward (``Cell`` or text), or ``None``.
        :param forward_amount: Amount to forward in nanotons.
        :param amount: Total amount to send in nanotons.
        :param query_id: Query identifier.
        :param send_mode: Send mode flags.
        :param bounce: Bounce on error, or ``None`` for auto-detect.
        :param encrypt: Encrypt the text ``forward_payload`` for the new owner.
        :param recipient_public_key: New owner public key for ``encrypt``, or ``None`` to fetch it.
        """
        self.destination = destination
        self.nft_address = nft_address
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.amount = amount
        self.query_id = query_id
        self.send_mode = send_mode
        self.bounce = bounce
        self.encrypt = encrypt
        self.recipient_public_key = recipient_public_key

    async def build(self, wallet: WalletProtocol[t.Any, t.Any, t.Any]) -> WalletMessage:
        """Build an NFT transfer ``WalletMessage``.

        :param wallet: Source wallet instance.
        :return: Constructed ``WalletMessage``.
        :raises ValueError: If ``encrypt`` is set without a text comment.
        :raises ContractError: If the destination or recipient public key cannot be resolved,
            or ``encrypt`` is set on a wallet without a private key.
        """
        destination = await _resolve_destination(wallet, self.destination)
        forward_payload = await _build_payload(
            wallet, self.forward_payload, destination, self.encrypt, self.recipient_public_key
        )
        body = NFTTransferBody(
            destination=destination,
            response_address=self.response_address or wallet.address,
            custom_payload=self.custom_payload,
            forward_payload=forward_payload,
            forward_amount=self.forward_amount,
            query_id=self.query_id,
        )
        return WalletMessage(
            send_mode=self.send_mode,
            message=InternalMessage(
                dest=self.nft_address,
                value=self.amount,
                body=body.serialize(),
                bounce=self.bounce,
            ),
        )


class JettonTransferBuilder(BaseMessageBuilder):
    """Builder for jetton transfer messages."""

    def __init__(
        self,
        destination: AddressLike,
        jetton_amount: int,
        jetton_wallet_address: AddressLike | None = None,
        jetton_master_address: AddressLike | None = None,
        response_address: AddressLike | None = None,
        custom_payload: Cell | None = None,
        forward_payload: Cell | str | None = None,
        forward_amount: int = 1,
        amount: int = to_nano("0.05"),
        query_id: int = 0,
        send_mode: SendMode | int = DEFAULT_SENDMODE,
        bounce: bool | None = None,
        encrypt: bool = False,
        recipient_public_key: PublicKey | None = None,
    ) -> None:
        """Initialize the jetton transfer builder.

        :param destination: Recipient address or ``.ton``/``.t.me`` domain.
        :param jetton_amount: Jetton amount in base units.
        :param jetton_wallet_address: Sender's jetton wallet, or ``None``.
        :param jetton_master_address: Jetton master for wallet resolution, or ``None``.
        :param response_address: Address for excess funds, or ``None`` for wallet address.
        :param custom_payload: Custom payload cell, or ``None``.
        :param forward_payload: Payload to forward (``Cell`` or text), or ``None``.
        :param forward_amount: Amount to forward in nanotons.
        :param amount: Total amount to send in nanotons.
        :param query_id: Query identifier.
        :param send_mode: Send mode flags.
        :param bounce: Bounce on error, or ``None`` for auto-detect.
        :param encrypt: Encrypt the text ``forward_payload`` for the recipient.
        :param recipient_public_key: Recipient public key for ``encrypt``, or ``None`` to fetch it.
        :raises ValueError: If both or neither wallet/master addresses given.
        """
        if (jetton_wallet_address is None) == (jetton_master_address is None):
            raise ValueError("You must pass exactly one of `jetton_wallet_address` or `jetton_master_address`.")
        self.destination = destination
        self.jetton_amount = jetton_amount
        self.jetton_wallet_address = jetton_wallet_address
        self.jetton_master_address = jetton_master_address
        self.response_address = response_address
        self.custom_payload = custom_payload
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.amount = amount
        self.query_id = query_id
        self.send_mode = send_mode
        self.bounce = bounce
        self.encrypt = encrypt
        self.recipient_public_key = recipient_public_key

    async def build(self, wallet: WalletProtocol[t.Any, t.Any, t.Any]) -> WalletMessage:
        """Build a jetton transfer ``WalletMessage``.

        :param wallet: Source wallet instance.
        :return: Constructed ``WalletMessage``.
        :raises ValueError: If ``encrypt`` is set without a text comment.
        :raises ContractError: If the destination or recipient public key cannot be resolved,
            or ``encrypt`` is set on a wallet without a private key.
        """
        jetton_wallet_address = self.jetton_wallet_address
        if self.jetton_wallet_address is None:
            assert self.jetton_master_address is not None
            jetton_wallet_address = await get_wallet_address_get_method(
                client=wallet.client,
                address=self.jetton_master_address,
                owner_address=wallet.address,
            )
        destination = await _resolve_destination(wallet, self.destination)
        forward_payload = await _build_payload(
            wallet, self.forward_payload, destination, self.encrypt, self.recipient_public_key
        )
        body = JettonTransferBody(
            destination=destination,
            jetton_amount=self.jetton_amount,
            response_address=self.response_address or wallet.address,
            custom_payload=self.custom_payload,
            forward_payload=forward_payload,
            forward_amount=self.forward_amount,
            query_id=self.query_id,
        )
        return WalletMessage(
            send_mode=self.send_mode,
            message=InternalMessage(
                dest=jetton_wallet_address,
                value=self.amount,
                body=body.serialize(),
                bounce=self.bounce,
            ),
        )
