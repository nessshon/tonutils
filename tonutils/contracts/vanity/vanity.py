from __future__ import annotations

import typing as t

from ton_core import (
    Address,
    StateInit,
    TickTock,
)

from tonutils.contracts.base import BaseContract

if t.TYPE_CHECKING:
    from tonutils.clients.protocol import ClientProtocol
    from tonutils.contracts.vanity.models import VanityResult


class Vanity(BaseContract[t.Any]):
    """Wrapper for deploying contracts at precomputed vanity addresses."""

    @classmethod
    def from_result(
        cls,
        client: ClientProtocol,
        result: VanityResult,
    ) -> Vanity:
        """Construct from a ``VanityResult``.

        :param client: TON client.
        :param result: Vanity generation result.
        :return: New contract instance.
        """
        address = Address(result.address)
        state_init = StateInit(code=result.init.code_cell)

        if result.init.split_depth:
            state_init.split_depth = result.init.split_depth
        if result.init.special:
            state_init.special = TickTock(
                tick=result.init.special.tick,
                tock=result.init.special.tock,
            )

        return cls(
            client=client,
            address=address,
            state_init=state_init,
        )
