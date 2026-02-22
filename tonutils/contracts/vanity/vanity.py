from __future__ import annotations

from pytoniq_core import StateInit, Address
from pytoniq_core.tlb.account import TickTock

from tonutils.clients.protocol import ClientProtocol
from tonutils.contracts.base import BaseContract
from tonutils.contracts.vanity.models import VanityResult


class Vanity(BaseContract):
    """Vanity contract wrapper."""

    @classmethod
    def from_result(
        cls,
        client: ClientProtocol,
        result: VanityResult,
    ) -> Vanity:
        """Construct from a `VanityResult`.

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
