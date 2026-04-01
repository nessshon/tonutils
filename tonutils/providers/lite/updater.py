from __future__ import annotations

import asyncio
import typing as t

from tonutils.transports.worker import BaseWorker
from tonutils.types import MasterchainInfo

if t.TYPE_CHECKING:
    from ton_core import BlockIdExt

    from tonutils.providers.lite.provider import LiteProvider


class UpdaterWorker(BaseWorker):
    """Masterchain update worker for ADNL providers.

    Tracks the latest masterchain block by subscribing to new seqno
    notifications through the lite-server.
    """

    def __init__(self, provider: LiteProvider) -> None:
        """Initialize the updater worker.

        :param provider: Parent ADNL provider.
        """
        super().__init__(provider)
        self._last_mc_block: BlockIdExt | None = None

    @property
    def last_mc_block(self) -> BlockIdExt | None:
        """Most recently known masterchain block."""
        return self._last_mc_block

    async def refresh(self) -> None:
        """Fetch current masterchain info and update the last block reference."""
        info = await self.provider.get_masterchain_info(priority=True)
        self._last_mc_block = info.last_block()

    async def _run(self) -> None:
        """Wait for new masterchain seqno updates and refresh block info."""
        provider = self.provider

        while self.running:
            try:
                if self._last_mc_block is None:
                    await self.refresh()
                    continue

                last_mc_block = self._last_mc_block
                raw = await provider.wait_masterchain_seqno(
                    seqno=last_mc_block.seqno + 1,
                    timeout_ms=10_000,
                    schema_name="getMasterchainInfo",
                    priority=True,
                )
                info = MasterchainInfo.from_dict(raw)
                self._last_mc_block = info.last_block()

            except asyncio.TimeoutError:
                continue
