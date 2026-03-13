from __future__ import annotations

import asyncio
import typing as t

from pytoniq_core import Cell, StateInit, WalletMessage

from tonutils.exceptions import ContractError
from tonutils.types import AddressLike, SendMode, DEFAULT_SENDMODE

if t.TYPE_CHECKING:
    from tonutils.contracts.wallet.base import BaseWallet
    from tonutils.contracts.wallet.messages import ExternalMessage, BaseMessageBuilder


class SeqnoGuard:
    """Seqno-aware guard for sequential wallet sends.

    Wraps a wallet and mirrors its transfer methods, ensuring each
    send is confirmed on-chain (seqno advances) before the next.

    :param wallet: Wallet with ``seqno`` get-method support.
    :param timeout: Maximum seqno wait time in seconds per send.
    :param poll_interval: Delay between seqno polls in seconds.
    :raises ContractError: If the wallet does not support ``seqno``.
    """

    def __init__(
        self,
        wallet: BaseWallet,
        timeout: float = 30.0,
        poll_interval: float = 1.5,
    ) -> None:
        if not hasattr(wallet, "seqno"):
            raise ContractError(
                wallet,
                "Wallet does not support `seqno` get-method.",
            )
        self._wallet = wallet
        self._lock = asyncio.Lock()
        self._timeout = timeout
        self._poll_interval = poll_interval

    async def _wait_seqno(self, current_seqno: int) -> None:
        """Poll until seqno advances or timeout is reached."""
        deadline = asyncio.get_event_loop().time() + self._timeout
        while asyncio.get_event_loop().time() < deadline:
            new_seqno = await self._wallet.seqno()  # type: ignore[attr-defined]
            if new_seqno != current_seqno:
                return
            await asyncio.sleep(self._poll_interval)
        raise ContractError(
            self._wallet,
            f"seqno did not change within {self._timeout}s "
            f"(stuck at {current_seqno}).",
        )

    async def _send(self, coro: t.Awaitable[ExternalMessage]) -> ExternalMessage:
        """Acquire lock, send, wait for seqno confirmation."""
        async with self._lock:
            seqno = await self._wallet.seqno()  # type: ignore[attr-defined]
            result = await coro
            await self._wait_seqno(seqno)
            return result

    async def transfer(
        self,
        destination: AddressLike,
        amount: int,
        body: t.Optional[t.Union[Cell, str]] = None,
        state_init: t.Optional[StateInit] = None,
        send_mode: t.Union[SendMode, int] = DEFAULT_SENDMODE,
        bounce: t.Optional[bool] = None,
        params: t.Optional[t.Any] = None,
    ) -> ExternalMessage:
        """Send a simple TON transfer with seqno confirmation.

        :param destination: Recipient address.
        :param amount: Amount in nanotons.
        :param body: Message body (`Cell` or text comment), or `None`.
        :param state_init: `StateInit` for deployment, or `None`.
        :param send_mode: Send mode flags.
        :param bounce: Bounce on error, or `None` for auto-detect.
        :param params: Transaction parameters, or `None`.
        :return: Sent `ExternalMessage`.
        """
        return await self._send(
            self._wallet.transfer(
                destination=destination,
                amount=amount,
                body=body,
                state_init=state_init,
                send_mode=send_mode,
                bounce=bounce,
                params=params,
            )
        )

    async def transfer_message(
        self,
        message: t.Union[WalletMessage, BaseMessageBuilder],
        params: t.Optional[t.Any] = None,
    ) -> ExternalMessage:
        """Send a single transfer with seqno confirmation.

        :param message: Internal message or message builder.
        :param params: Transaction parameters, or `None`.
        :return: Sent `ExternalMessage`.
        """
        return await self._send(
            self._wallet.transfer_message(
                message=message,
                params=params,
            )
        )

    async def batch_transfer_message(
        self,
        messages: t.Sequence[t.Union[WalletMessage, BaseMessageBuilder]],
        params: t.Optional[t.Any] = None,
    ) -> ExternalMessage:
        """Send a batch transfer with seqno confirmation.

        :param messages: Internal messages or message builders.
        :param params: Transaction parameters, or `None`.
        :return: Sent `ExternalMessage`.
        """
        return await self._send(
            self._wallet.batch_transfer_message(
                messages=messages,
                params=params,
            )
        )
