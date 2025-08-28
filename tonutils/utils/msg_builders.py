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

from ..types.common import DEFAULT_SENDMODE


def build_external_msg_any(
    src: t.Optional[Address] = None,
    dest: t.Optional[Address] = None,
    import_fee: int = 0,
    body: t.Optional[Cell] = None,
    state_init: t.Optional[StateInit] = None,
) -> MessageAny:
    info = ExternalMsgInfo(src=src, dest=dest, import_fee=import_fee)
    return MessageAny(info, state_init, body)


def build_internal_msg_any(
    ihr_disabled: t.Optional[bool] = True,
    bounce: t.Optional[bool] = None,
    bounced: t.Optional[bool] = False,
    src: t.Optional[Address] = None,
    dest: t.Optional[Address] = None,
    value: t.Union[CurrencyCollection, int] = 0,
    ihr_fee: int = 0,
    fwd_fee: int = 0,
    created_lt: int = 0,
    created_at: int = 0,
    body: t.Optional[Cell] = None,
    state_init: t.Optional[StateInit] = None,
) -> MessageAny:
    if isinstance(value, int):
        value = CurrencyCollection(value)
    if bounce is None:
        bounce = dest.is_bounceable if dest else False
    if body is None:
        body = Cell.empty()

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
    return MessageAny(info, state_init, body)


def build_internal_wallet_msg(
    dest: Address,
    send_mode: t.Optional[int] = None,
    value: int = 0,
    body: t.Optional[Cell] = None,
    state_init: t.Optional[StateInit] = None,
    bounce: t.Optional[bool] = None,
) -> WalletMessage:
    if send_mode is None:
        send_mode = DEFAULT_SENDMODE

    message = build_internal_msg_any(
        bounce=bounce,
        dest=dest,
        value=value,
        body=body,
        state_init=state_init,
    )
    return WalletMessage(send_mode, message)
