import abc
import typing as t

from pytoniq_core import (
    Address,
    Cell,
    CurrencyCollection,
    ExternalMsgInfo,
    InternalMsgInfo,
    MessageAny,
    StateInit,
    WalletMessage,
)

from tonutils.contracts.jetton.methods import get_wallet_address_get_method
from tonutils.contracts.jetton.tlb import JettonTransferBody
from tonutils.contracts.nft.tlb import NFTTransferBody
from tonutils.contracts.wallet.protocol import WalletProtocol
from tonutils.contracts.wallet.tlb import TextCommentBody
from tonutils.types import AddressLike, SendMode, DEFAULT_SENDMODE
from tonutils.utils import cell_to_hex, cell_to_b64, normalize_hash, to_nano


class ExternalMessage(MessageAny):
    """External message for sending transactions to the TON blockchain."""

    def __init__(
        self,
        src: t.Optional[Address] = None,
        dest: t.Optional[Address] = None,
        import_fee: int = 0,
        body: t.Optional[Cell] = None,
        state_init: t.Optional[StateInit] = None,
    ) -> None:
        """
        :param src: Source address, or `None`.
        :param dest: Destination contract address, or `None`.
        :param import_fee: Import fee in nanotons.
        :param body: Signed message body cell, or `None`.
        :param state_init: `StateInit` for deployment, or `None`.
        """
        if isinstance(src, str):
            src = Address(src)
        if isinstance(dest, str):
            dest = Address(dest)
        info = ExternalMsgInfo(src, dest, import_fee)
        super().__init__(info, state_init, body)

    def to_cell(self) -> Cell:
        """Serialize to `Cell`."""
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

    @property
    def normalized_hash(self) -> str:
        """Normalized message hash as hex string."""
        return normalize_hash(self)


class InternalMessage(MessageAny):
    """Internal message for on-chain contract-to-contract communication."""

    def __init__(
        self,
        ihr_disabled: t.Optional[bool] = True,
        bounce: t.Optional[bool] = None,
        bounced: t.Optional[bool] = False,
        src: t.Optional[AddressLike] = None,
        dest: t.Optional[AddressLike] = None,
        value: t.Union[CurrencyCollection, int] = 0,
        ihr_fee: int = 0,
        fwd_fee: int = 0,
        created_lt: int = 0,
        created_at: int = 0,
        body: t.Optional[Cell] = None,
        state_init: t.Optional[StateInit] = None,
    ) -> None:
        """
        :param ihr_disabled: Disable instant hypercube routing.
        :param bounce: Bounce on error, or `None` for auto-detect.
        :param bounced: Whether this is a bounced message.
        :param src: Source address, or `None`.
        :param dest: Destination address, or `None`.
        :param value: Amount in nanotons or `CurrencyCollection`.
        :param ihr_fee: IHR fee in nanotons.
        :param fwd_fee: Forward fee in nanotons.
        :param created_lt: Logical time when created.
        :param created_at: Unix timestamp when created.
        :param body: Message body cell, or `None`.
        :param state_init: `StateInit` for deployment, or `None`.
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
    """Abstract base for constructing `WalletMessage` instances."""

    @abc.abstractmethod
    async def build(self, wallet: WalletProtocol) -> WalletMessage:
        """Build a `WalletMessage` for the given wallet.

        :param wallet: Source wallet instance.
        :return: Constructed `WalletMessage`.
        """


class TONTransferBuilder(BaseMessageBuilder):
    """Builder for simple TON transfer messages."""

    def __init__(
        self,
        destination: AddressLike,
        amount: int,
        body: t.Optional[t.Union[Cell, str]] = None,
        state_init: t.Optional[StateInit] = None,
        send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE,
        bounce: t.Optional[bool] = None,
    ) -> None:
        """
        :param destination: Recipient address.
        :param amount: Amount in nanotons.
        :param body: Body (`Cell` or text comment), or `None`.
        :param state_init: `StateInit` for deployment, or `None`.
        :param send_mode: Send mode flags.
        :param bounce: Bounce on error, or `None` for auto-detect.
        """
        if isinstance(body, str):
            body = TextCommentBody(body).serialize()
        self.destination = destination
        self.amount = amount
        self.body = body
        self.state_init = state_init
        self.send_mode = send_mode
        self.bounce = bounce

    async def build(self, wallet: WalletProtocol) -> WalletMessage:
        """Build a TON transfer `WalletMessage`.

        :param wallet: Source wallet instance.
        :return: Constructed `WalletMessage`.
        """
        return WalletMessage(
            send_mode=self.send_mode,
            message=InternalMessage(
                dest=self.destination,
                value=self.amount,
                body=self.body,
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
        response_address: t.Optional[AddressLike] = None,
        custom_payload: t.Optional[Cell] = None,
        forward_payload: t.Optional[t.Union[Cell, str]] = None,
        forward_amount: int = 1,
        amount: int = to_nano("0.05"),
        query_id: int = 0,
        send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE,
        bounce: t.Optional[bool] = None,
    ) -> None:
        """
        :param destination: New NFT owner address.
        :param nft_address: NFT item contract address.
        :param response_address: Address for excess funds, or `None` for wallet address.
        :param custom_payload: Custom payload cell, or `None`.
        :param forward_payload: Payload to forward (`Cell` or text), or `None`.
        :param forward_amount: Amount to forward in nanotons.
        :param amount: Total amount to send in nanotons.
        :param query_id: Query identifier.
        :param send_mode: Send mode flags.
        :param bounce: Bounce on error, or `None` for auto-detect.
        """
        if isinstance(forward_payload, str):
            forward_payload = TextCommentBody(forward_payload).serialize()
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

    async def build(self, wallet: WalletProtocol) -> WalletMessage:
        """Build an NFT transfer `WalletMessage`.

        :param wallet: Source wallet instance.
        :return: Constructed `WalletMessage`.
        """
        body = NFTTransferBody(
            destination=self.destination,
            response_address=self.response_address or wallet.address,
            custom_payload=self.custom_payload,
            forward_payload=self.forward_payload,
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
        jetton_wallet_address: t.Optional[AddressLike] = None,
        jetton_master_address: t.Optional[AddressLike] = None,
        response_address: t.Optional[AddressLike] = None,
        custom_payload: t.Optional[Cell] = None,
        forward_payload: t.Optional[t.Union[Cell, str]] = None,
        forward_amount: int = 1,
        amount: int = to_nano("0.05"),
        query_id: int = 0,
        send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE,
        bounce: t.Optional[bool] = None,
    ) -> None:
        """
        :param destination: Recipient address.
        :param jetton_amount: Jetton amount in base units.
        :param jetton_wallet_address: Sender's jetton wallet, or `None`.
        :param jetton_master_address: Jetton master for wallet resolution, or `None`.
        :param response_address: Address for excess funds, or `None` for wallet address.
        :param custom_payload: Custom payload cell, or `None`.
        :param forward_payload: Payload to forward (`Cell` or text), or `None`.
        :param forward_amount: Amount to forward in nanotons.
        :param amount: Total amount to send in nanotons.
        :param query_id: Query identifier.
        :param send_mode: Send mode flags.
        :param bounce: Bounce on error, or `None` for auto-detect.
        :raises ValueError: If both or neither wallet/master addresses given.
        """
        if (jetton_wallet_address is None) == (jetton_master_address is None):
            raise ValueError(
                "You must pass exactly one of "
                "`jetton_wallet_address` or `jetton_master_address`."
            )
        if isinstance(forward_payload, str):
            forward_payload = TextCommentBody(forward_payload).serialize()
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

    async def build(self, wallet: WalletProtocol) -> WalletMessage:
        """Build a jetton transfer `WalletMessage`.

        :param wallet: Source wallet instance.
        :return: Constructed `WalletMessage`.
        """
        jetton_wallet_address = self.jetton_wallet_address
        if self.jetton_wallet_address is None:
            jetton_wallet_address = await get_wallet_address_get_method(
                client=wallet.client,
                address=self.jetton_master_address,
                owner_address=wallet.address,
            )
        body = JettonTransferBody(
            destination=self.destination,
            jetton_amount=self.jetton_amount,
            response_address=self.response_address or wallet.address,
            custom_payload=self.custom_payload,
            forward_payload=self.forward_payload,
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
