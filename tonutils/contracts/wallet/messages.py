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
from tonutils.contracts.wallet.tlb import TextCommentBody
from tonutils.protocols.wallet import WalletProtocol
from tonutils.types import AddressLike, SendMode, DEFAULT_SENDMODE
from tonutils.utils import (
    cell_to_hex,
    cell_to_b64,
    normalize_hash,
    to_nano,
    resolve_wallet_address,
)


class ExternalMessage(MessageAny):
    """External message for sending transactions to TON blockchain."""

    def __init__(
        self,
        src: t.Optional[Address] = None,
        dest: t.Optional[Address] = None,
        import_fee: int = 0,
        body: t.Optional[Cell] = None,
        state_init: t.Optional[StateInit] = None,
    ) -> None:
        """
        Initialize external message.

        :param src: Source address (typically None for external messages)
        :param dest: Destination contract address
        :param import_fee: Import fee in nanotons (default: 0)
        :param body: Message body cell (signed transaction data)
        :param state_init: Optional StateInit for contract deployment
        """
        if isinstance(src, str):
            src = Address(src)
        if isinstance(dest, str):
            dest = Address(dest)
        info = ExternalMsgInfo(src, dest, import_fee)
        super().__init__(info, state_init, body)

    def to_cell(self) -> Cell:
        """
        Serialize message to Cell.

        :return: Serialized message cell
        """
        return self.serialize()

    def to_boc(self) -> bytes:
        """
        Serialize message to BOC (Bag of Cells) bytes.

        :return: BOC-encoded message bytes
        """
        return self.to_cell().to_boc()

    @property
    def as_hex(self) -> str:
        """
        Get message as hex-encoded BOC string.

        :return: Hex-encoded BOC string
        """
        return cell_to_hex(self.to_cell())

    @property
    def as_b64(self) -> str:
        """
        Get message as base64-encoded BOC string.

        :return: Base64-encoded BOC string
        """
        return cell_to_b64(self.to_cell())

    @property
    def normalized_hash(self) -> str:
        """
        Get normalized hash of the message.

        :return: Normalized message hash as hex string
        """
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
        Initialize internal message.

        :param ihr_disabled: Disable instant hypercube routing (default: True)
        :param bounce: Whether to bounce on error (auto-detected from dest if None)
        :param bounced: Whether this is a bounced message (default: False)
        :param src: Source address (set by blockchain if None)
        :param dest: Destination address
        :param value: Amount to send (nanotons or CurrencyCollection)
        :param ihr_fee: IHR fee in nanotons (default: 0)
        :param fwd_fee: Forward fee in nanotons (default: 0)
        :param created_lt: Logical time when created (default: 0)
        :param created_at: Unix timestamp when created (default: 0)
        :param body: Message body cell (default: empty cell)
        :param state_init: Optional StateInit for contract deployment
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
    """
    Abstract base class for message builders.

    Message builders construct WalletMessage instances with proper
    parameters for specific operations (transfers, NFT, jettons, etc.).
    """

    @abc.abstractmethod
    async def build(self, wallet: WalletProtocol) -> WalletMessage:
        """
        Build a WalletMessage for the given wallet.

        :param wallet: Wallet instance to build message for
        :return: Constructed WalletMessage ready for sending
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
        Initialize TON transfer builder.

        :param destination: Recipient address (Address, string, or domain)
        :param amount: Amount to send in nanotons
        :param body: Optional message body (Cell or text comment string)
        :param state_init: Optional StateInit for contract deployment
        :param send_mode: Message send mode (default: pay fees separately)
        :param bounce: Whether to bounce on error (auto-detected if None)
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
        """
        Build TON transfer message.

        :param wallet: Wallet instance to build message for
        :return: WalletMessage with TON transfer
        """
        destination = await resolve_wallet_address(wallet.client, self.destination)
        return WalletMessage(
            send_mode=self.send_mode,
            message=InternalMessage(
                dest=destination,
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
        Initialize NFT transfer builder.

        :param destination: New NFT owner address
        :param nft_address: NFT item contract address
        :param response_address: Address for excess funds (default: wallet address)
        :param custom_payload: Optional custom payload cell
        :param forward_payload: Optional payload to forward (Cell or text string)
        :param forward_amount: Amount to forward in nanotons (default: 1)
        :param amount: Total amount to send in nanotons (default: 0.05 TON)
        :param query_id: Query identifier (default: 0)
        :param send_mode: Message send mode (default: pay fees separately)
        :param bounce: Whether to bounce on error (auto-detected if None)
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
        """
        Build NFT transfer message.

        :param wallet: Wallet instance to build message for
        :return: WalletMessage with NFT transfer
        """
        destination = await resolve_wallet_address(wallet.client, self.destination)
        body = NFTTransferBody(
            destination=destination,
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
    """Builder for jetton (fungible token) transfer messages."""

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
        Initialize jetton transfer builder.

        :param destination: Recipient address
        :param jetton_amount: Amount of jettons to transfer (in jetton's base units)
        :param jetton_wallet_address: Sender's jetton wallet address (optional)
        :param jetton_master_address: Jetton minter address (optional, used to resolve wallet)
        :param response_address: Address for excess funds (default: wallet address)
        :param custom_payload: Optional custom payload cell
        :param forward_payload: Optional payload to forward (Cell or text string)
        :param forward_amount: Amount to forward in nanotons (default: 1)
        :param amount: Total amount to send in nanotons (default: 0.05 TON)
        :param query_id: Query identifier (default: 0)
        :param send_mode: Message send mode (default: pay fees separately)
        :param bounce: Whether to bounce on error (auto-detected if None)
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
        """
        Build jetton transfer message.

        :param wallet: Wallet instance to build message for
        :return: WalletMessage with jetton transfer
        """
        destination = await resolve_wallet_address(wallet.client, self.destination)
        jetton_wallet_address = self.jetton_wallet_address
        if self.jetton_wallet_address is None:
            jetton_wallet_address = await get_wallet_address_get_method(
                client=wallet.client,
                address=self.jetton_master_address,
                owner_address=wallet.address,
            )
        body = JettonTransferBody(
            destination=destination,
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
