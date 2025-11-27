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

    def __init__(
        self,
        src: t.Optional[Address] = None,
        dest: t.Optional[Address] = None,
        import_fee: int = 0,
        body: t.Optional[Cell] = None,
        state_init: t.Optional[StateInit] = None,
    ) -> None:
        if isinstance(src, str):
            src = Address(src)
        if isinstance(dest, str):
            dest = Address(dest)
        info = ExternalMsgInfo(src, dest, import_fee)
        super().__init__(info, state_init, body)

    def to_cell(self) -> Cell:
        return self.serialize()

    def to_boc(self) -> bytes:
        return self.to_cell().to_boc()

    @property
    def as_hex(self) -> str:
        return cell_to_hex(self.to_cell())

    @property
    def as_b64(self) -> str:
        return cell_to_b64(self.to_cell())

    @property
    def normalized_hash(self) -> str:
        return normalize_hash(self)


class InternalMessage(MessageAny):

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

    @abc.abstractmethod
    async def build(self, wallet: WalletProtocol) -> WalletMessage: ...


class TONTransferBuilder(BaseMessageBuilder):

    def __init__(
        self,
        destination: AddressLike,
        amount: int,
        body: t.Optional[t.Union[Cell, str]] = None,
        state_init: t.Optional[StateInit] = None,
        send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE,
        bounce: t.Optional[bool] = None,
    ) -> None:
        if isinstance(body, str):
            body = TextCommentBody(body).serialize()
        self.destination = destination
        self.amount = amount
        self.body = body
        self.state_init = state_init
        self.send_mode = send_mode
        self.bounce = bounce

    async def build(self, wallet: WalletProtocol) -> WalletMessage:
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
