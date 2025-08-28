import abc
import typing as t

from pytoniq_core import (
    Address,
    Cell,
    StateInit,
    WalletMessage,
)

from ..types.common import AddressLike, SendMode
from ..types.tlb.text import TextComment
from ..utils.value_utils import to_nano

if t.TYPE_CHECKING:
    from ..protocols import WalletProtocol

    W = t.TypeVar("W", bound=WalletProtocol)
else:
    W = t.TypeVar("W")


class BaseTransferMessage(abc.ABC):

    @abc.abstractmethod
    async def to_wallet_msg(
        self,
        wallet: W,
    ) -> WalletMessage: ...


class TransferMessage(BaseTransferMessage):

    def __init__(
        self,
        destination: AddressLike,
        value: int,
        body: t.Optional[t.Union[Cell, str]] = None,
        state_init: t.Optional[StateInit] = None,
        send_mode: t.Optional[t.Union[SendMode, int]] = None,
        bounce: t.Optional[bool] = None,
    ) -> None:
        if isinstance(destination, str):
            destination = Address(destination)
        if isinstance(body, str):
            body = TextComment(body).serialize()

        self.destination = destination
        self.value = value
        self.body = body
        self.state_init = state_init
        self.send_mode = send_mode
        self.bounce = bounce

    async def to_wallet_msg(
        self,
        wallet: W,
    ) -> WalletMessage:
        from ..utils.msg_builders import build_internal_wallet_msg

        return build_internal_wallet_msg(
            dest=self.destination,
            value=self.value,
            body=self.body,
            state_init=self.state_init,
            send_mode=self.send_mode,
            bounce=self.bounce,
        )


class TransferNFTMessage(BaseTransferMessage):

    def __init__(
        self,
        destination: AddressLike,
        nft_address: AddressLike,
        response_address: t.Optional[AddressLike] = None,
        forward_payload: t.Optional[t.Union[Cell, str]] = None,
        forward_amount: t.Union[int, float] = 1,
        value: t.Union[int, float] = to_nano(0.05),
        send_mode: t.Optional[t.Union[SendMode, int]] = None,
        bounce: t.Optional[bool] = None,
    ) -> None:
        if isinstance(nft_address, str):
            nft_address = Address(nft_address)
        if isinstance(forward_payload, str):
            forward_payload = TextComment(forward_payload).serialize()

        self.destination = destination
        self.nft_address = nft_address
        self.response_address = response_address
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.value = value
        self.send_mode = send_mode
        self.bounce = bounce

    async def to_wallet_msg(
        self,
        wallet: W,
    ) -> WalletMessage:
        raise NotImplementedError


class TransferJettonMessage(BaseTransferMessage):

    def __init__(
        self,
        destination: AddressLike,
        jetton_master_address: AddressLike,
        jetton_amount: t.Union[int, float],
        jetton_decimals: int = 9,
        jetton_wallet_address: t.Optional[AddressLike] = None,
        forward_payload: t.Optional[t.Union[Cell, str]] = None,
        forward_amount: t.Union[int, float] = 1,
        value: t.Union[int, float] = to_nano(0.05),
        send_mode: t.Optional[t.Union[SendMode, int]] = None,
        bounce: t.Optional[bool] = None,
    ) -> None:
        if isinstance(jetton_master_address, str):
            jetton_master_address = Address(jetton_master_address)
        if isinstance(jetton_wallet_address, str):
            jetton_wallet_address = Address(jetton_wallet_address)
        if isinstance(forward_payload, str):
            forward_payload = TextComment(forward_payload).serialize()

        self.destination = destination
        self.jetton_master_address = jetton_master_address
        self.jetton_amount = jetton_amount
        self.jetton_decimals = jetton_decimals
        self.jetton_wallet_address = jetton_wallet_address
        self.forward_payload = forward_payload
        self.forward_amount = forward_amount
        self.value = value
        self.send_mode = send_mode
        self.bounce = bounce

    async def to_wallet_msg(
        self,
        wallet: W,
    ) -> WalletMessage:
        raise NotImplementedError
