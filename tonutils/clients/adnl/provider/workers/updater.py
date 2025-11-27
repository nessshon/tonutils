from __future__ import annotations

import asyncio
import typing as t

from pytoniq_core import BlockIdExt

from tonutils.clients.adnl.provider.models import MasterchainInfo
from tonutils.clients.adnl.provider.workers.base import BaseWorker

if t.TYPE_CHECKING:
    from tonutils.clients.adnl.provider import AdnlProvider


class UpdaterWorker(BaseWorker):

    def __init__(self, provider: AdnlProvider) -> None:
        super().__init__(provider)
        self._last_mc_block: t.Optional[BlockIdExt] = None

    @property
    def last_mc_block(self) -> t.Optional[BlockIdExt]:
        return self._last_mc_block

    async def refresh(self) -> None:
        info = await self.provider.get_masterchain_info(priority=True)
        self._last_mc_block = info.last_block()

    async def _run(self) -> None:
        provider = self.provider

        while self.running:
            try:
                if self._last_mc_block is None:
                    await self.refresh()
                    continue

                last_mc_block = t.cast(BlockIdExt, self._last_mc_block)
                raw = await provider.wait_masterchain_seqno(
                    seqno=last_mc_block.seqno + 1,
                    timeout_ms=10_000,
                    schema_name="getMasterchainInfo",
                    priority=True,
                )
                info = MasterchainInfo(**raw)
                self._last_mc_block = info.last_block()

            except asyncio.TimeoutError:
                continue
