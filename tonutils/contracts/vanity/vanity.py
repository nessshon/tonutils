from __future__ import annotations

from pytoniq_core import StateInit, Address
from pytoniq_core.tlb.account import TickTock

from tonutils.contracts.base import BaseContract
from tonutils.contracts.vanity.models import VanityResult
from tonutils.protocols.client import ClientProtocol


class Vanity(BaseContract):
    """Vanity contract."""

    @classmethod
    def from_result(
        cls,
        client: ClientProtocol,
        result: VanityResult,
    ) -> Vanity:
        """
        Construct Vanity contract wrapper from generated result.

        :param client: TON client to bind to the contract
        :param result: Vanity generation result with address and init data
        :return: Vanity contract instance
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
